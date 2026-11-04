"""Verifica originales y equivalencia de inferencia demo; no carga ni evalúa TEST."""
import hashlib
import json
from pathlib import Path
import pandas as pd
from common.config import ROOT
from edge_service.app.model_loader import ModelBundle

def main():
    source=ROOT.parent/"MantenIA_ML"
    inventory=json.loads((ROOT/"docs/original_inventory.json").read_text(encoding="utf-8"))
    changed=[item["path"] for item in inventory if hashlib.sha256((source/item["path"]).read_bytes()).hexdigest()!=item["sha256"]]
    bundle=ModelBundle(ROOT/"edge_service/models")
    inputs=pd.read_csv(ROOT/"data/demo/demo_input.csv")
    expected=pd.read_csv(source/"results/predictions/demo_predictions.csv")
    probabilities=bundle.pipeline.predict_proba(inputs)[:,bundle.positive_index]
    difference=float(abs(probabilities-expected.probabilidad_falla.to_numpy()).max())
    outcome={"original_files_checked":len(inventory),"original_files_changed":changed,
             "model_version":bundle.version,"threshold":bundle.threshold,
             "demo_records_compared":len(inputs),"max_probability_difference":difference,
             "equivalent":difference<1e-12,"retrained":False,"test_reevaluated":False}
    (ROOT/"results/integration/frozen_model_verification.json").write_text(json.dumps(outcome,indent=2),encoding="utf-8")
    print(json.dumps(outcome,indent=2))
    if changed or not outcome["equivalent"]:raise SystemExit(1)
if __name__=="__main__":main()
