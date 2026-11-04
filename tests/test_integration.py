import csv
import io
import json
import sqlite3
from decimal import Decimal
import httpx
import joblib
import pandas as pd
import pytest
from common.config import ROOT, Settings
from common.schemas import MachineRecord
from backend.app.database import Database
from backend.app.metrics import reports

@pytest.fixture
def record():
    row = pd.read_csv(ROOT / "data/demo/demo_input.csv").iloc[0].to_dict()
    return row

def csv_data(n=12, extra=False):
    rows = list(csv.DictReader((ROOT / "data/demo/demo_input.csv").open(encoding="utf-8")))
    fields = list(rows[0])
    if extra: fields.append("Machine failure")
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields); writer.writeheader()
    writer.writerows([rows[i % len(rows)] for i in range(n)])
    return output.getvalue().encode()

def test_health_and_frontend(stack):
    client = stack["client"]
    assert client.get("/health").json()["status"] == "ok"
    page = client.get("/")
    assert page.status_code == 200 and "machine-form" in page.text
    assert "default-src 'self'" in page.headers["content-security-policy"]
    assert client.get("/static/app.js").status_code == 200

def test_model_info_and_real_prediction_persistence_usage(stack, record):
    client = stack["client"]
    info = client.get("/model/info").json()
    metadata = json.loads((ROOT / "edge_service/models/model_metadata.json").read_text(encoding="utf-8"))
    assert info["threshold"] == metadata["threshold"] == .425
    assert info["test_metrics"] == metadata["final_test_metrics"]
    before = client.get("/metrics/usage").json()
    response = client.post("/predict", json=record)
    assert response.status_code == 200, response.text
    result = response.json()
    pipeline = joblib.load(ROOT / "edge_service/models/mantenia_model.joblib")
    expected = pipeline.predict_proba(pd.DataFrame([record])[metadata["features"]])[0, 1]
    assert result["failure_probability"] == pytest.approx(expected, abs=1e-12)
    assert result["prediction"] == int(expected >= .425)
    assert result["inference_latency_ms"] > 0 and result["total_latency_ms"] >= result["inference_latency_ms"]
    detail = client.get("/predictions/" + result["request_id"]).json()
    assert detail["results"][0]["failure_probability"] == result["failure_probability"]
    assert detail["total_latency_ms"] == result["total_latency_ms"]
    after = client.get("/metrics/usage").json()
    assert after["billable_units"] - before["billable_units"] == 1
    with sqlite3.connect(stack["db"]) as db:
        assert db.execute("SELECT raw_inputs_json FROM prediction_requests WHERE request_id=?", (result["request_id"],)).fetchone()[0] is None
        assert db.execute("SELECT billable_units FROM usage_events WHERE request_id=?", (result["request_id"],)).fetchone()[0] == 1

@pytest.mark.parametrize("column,value", [("Machine failure", 1), ("UDI", 1), ("TWF", 0), ("Type","unknown"), ("Torque [Nm]",-1), ("Torque [Nm]", True), ("Torque [Nm]","42")])
def test_invalid_schema_no_charge(stack, record, column, value):
    client = stack["client"]; record[column] = value
    before = client.get("/metrics/usage").json()["billable_units"]
    response = client.post("/predict", json=record)
    assert response.status_code == 422
    assert "input" not in response.json()
    assert client.get("/metrics/usage").json()["billable_units"] == before
    assert client.get("/predictions/" + response.json()["request_id"]).json()["status"] == "failed"

def test_batch_1000_real_sorted_download(stack):
    client = stack["client"]
    before = client.get("/metrics/usage").json()["billable_units"]
    response = client.post("/predict/csv", files={"file": ("sensitive-client-name.csv", csv_data(1000), "text/csv")})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["record_count"] == 1000
    probabilities = [r["failure_probability"] for r in data["results"]]
    assert probabilities == sorted(probabilities, reverse=True)
    assert {r["row_index"] for r in data["results"]} == set(range(1,1001))
    assert client.get("/metrics/usage").json()["billable_units"] - before == 1000
    downloaded = client.get("/predictions/" + data["request_id"] + "/download")
    assert len(list(csv.DictReader(io.StringIO(downloaded.text)))) == 1000
    assert b"sensitive-client-name" not in stack["db"].read_bytes()

@pytest.mark.parametrize("payload,status", [(csv_data(1001),413), (csv_data(2,True),422), (b"wrong\nhello",422), (b"\xff\xfe",422), (csv_data(0),422)], ids=["too_many_rows","extra_column","wrong_header","invalid_encoding","empty_csv"])
def test_invalid_csv(stack, payload, status):
    assert stack["client"].post("/predict/csv", files={"file":("input.csv",payload,"text/csv")}).status_code == status

@pytest.mark.parametrize("value", ["nan","inf","-3","bad"])
def test_invalid_numeric_csv(stack, value):
    content = csv_data(1).decode().splitlines()
    cells = content[1].split(","); cells[1] = value
    payload = (content[0] + "\n" + ",".join(cells)).encode()
    assert stack["client"].post("/predict/csv",files={"file":("x.csv",payload)}).status_code == 422

def test_body_limit_and_cross_origin(stack, record):
    client=stack["client"]
    assert client.post("/predict",content=b"x"*2100000,headers={"Content-Type":"application/json"}).status_code==413
    assert client.post("/predict",json=record,headers={"Origin":"https://external.invalid"}).status_code==403

def test_finops_real_events_and_repricing(stack):
    client=stack["client"]; costs=client.get("/finops/summary").json()
    assert costs["estimated_cost"] == pytest.approx(costs["billable_units"] * .6)
    assert costs["total_compute_time_ms"] > 0
    assert client.get("/metrics/latency").json()["total"]["p95_ms"] > 0
    recalculated = reports(Database(stack["db"]), Decimal("1.20"))[2]
    assert recalculated["estimated_cost"] == pytest.approx(costs["billable_units"] * 1.2)
    assert recalculated["historical_estimated_cost"] == costs["historical_estimated_cost"]

def test_persistence_reopen_and_retention(stack, tmp_path):
    db=Database(stack["db"])
    assert db.history()
    assert Database(stack["db"]).history()[0] == db.history()[0]
    temporary=Database(tmp_path/"retention.db")
    temporary.finish("expired","individual","failed",1,"422")
    with temporary.connect() as connection:
        connection.execute("UPDATE prediction_requests SET timestamp='2000-01-01T00:00:00+00:00'")
    assert temporary.purge(30)==1
    assert temporary.history()==[]

def test_edge_endpoints_and_model_integrity(stack, record, tmp_path):
    from edge_service.app.model_loader import ModelBundle
    with httpx.Client(base_url=stack["edge"],trust_env=False) as client:
        assert client.get("/health").json()["model_loaded"]
        assert client.post("/infer",json=record).status_code==200
        assert client.post("/infer/batch",json={"records":[]}).status_code==422
    import shutil
    for filename in ("model_metadata.json","final_test_metrics.json","mantenia_model.joblib"):
        shutil.copyfile(ROOT/"edge_service/models"/filename,tmp_path/filename)
    with (tmp_path/"mantenia_model.joblib").open("ab") as f: f.write(b"tampered")
    with pytest.raises(RuntimeError,match="Integridad"): ModelBundle(tmp_path)

def test_external_edge_url_forbidden():
    with pytest.raises(ValueError): Settings(edge_url="https://external.invalid")

def test_raw_opt_in_stores_only_validated_fields(tmp_path, record):
    db=Database(tmp_path/"raw.db")
    result={"results":[{"row_index":1,"failure_probability":.1,"prediction":0}],
            "inference_latency_ms":1,"model_version":"test-db-only"}
    # Esta prueba de almacenamiento no representa predicción ni métricas del prototipo.
    db.save_success("raw","individual",result,[MachineRecord.model_validate(record).model_dump(by_alias=True)],True,Decimal(".60"))
    with db.connect() as connection:
        raw=json.loads(connection.execute("SELECT raw_inputs_json FROM prediction_requests").fetchone()[0])
    assert raw[0]==record
