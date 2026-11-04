import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta

def utcnow():
    return datetime.now(timezone.utc).isoformat()

class Database:
    def __init__(self, path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
            PRAGMA journal_mode=WAL;
            PRAGMA secure_delete=ON;
            CREATE TABLE IF NOT EXISTS model_info (
                version TEXT PRIMARY KEY, metadata_json TEXT NOT NULL, registered_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS prediction_requests (
                request_id TEXT PRIMARY KEY, timestamp TEXT NOT NULL, request_type TEXT NOT NULL,
                record_count INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL,
                total_latency_ms REAL, inference_latency_ms REAL, model_version TEXT,
                error_code TEXT, raw_inputs_json TEXT, client_id TEXT NOT NULL DEFAULT 'cliente_demo_01',
                records_received INTEGER NOT NULL DEFAULT 0, records_processed INTEGER NOT NULL DEFAULT 0,
                records_failed INTEGER NOT NULL DEFAULT 0, project TEXT NOT NULL DEFAULT 'MantenIA',
                environment TEXT NOT NULL DEFAULT 'development', component TEXT NOT NULL DEFAULT 'backend',
                resource TEXT NOT NULL DEFAULT 'cpu'
            );
            CREATE TABLE IF NOT EXISTS prediction_results (
                request_id TEXT NOT NULL REFERENCES prediction_requests(request_id) ON DELETE CASCADE,
                row_index INTEGER NOT NULL, failure_probability REAL NOT NULL, prediction INTEGER NOT NULL,
                PRIMARY KEY(request_id, row_index)
            );
            CREATE TABLE IF NOT EXISTS usage_events (
                request_id TEXT PRIMARY KEY REFERENCES prediction_requests(request_id) ON DELETE CASCADE,
                timestamp TEXT NOT NULL, billable_units INTEGER NOT NULL, inference_count INTEGER NOT NULL,
                compute_time_ms REAL NOT NULL, cost_rate_mxn TEXT NOT NULL, estimated_cost TEXT NOT NULL,
                client_id TEXT NOT NULL DEFAULT 'cliente_demo_01', project TEXT NOT NULL DEFAULT 'MantenIA',
                environment TEXT NOT NULL DEFAULT 'development', component TEXT NOT NULL DEFAULT 'backend', resource TEXT NOT NULL DEFAULT 'cpu'
            );
            CREATE INDEX IF NOT EXISTS request_timestamp ON prediction_requests(timestamp);
            """)
            existing = {r[1] for r in db.execute("PRAGMA table_info(prediction_requests)")}
            for name, ddl in {"client_id":"TEXT NOT NULL DEFAULT 'cliente_demo_01'", "records_received":"INTEGER NOT NULL DEFAULT 0", "records_processed":"INTEGER NOT NULL DEFAULT 0", "records_failed":"INTEGER NOT NULL DEFAULT 0", "project":"TEXT NOT NULL DEFAULT 'MantenIA'", "environment":"TEXT NOT NULL DEFAULT 'development'", "component":"TEXT NOT NULL DEFAULT 'backend'", "resource":"TEXT NOT NULL DEFAULT 'cpu'"}.items():
                if name not in existing: db.execute(f"ALTER TABLE prediction_requests ADD COLUMN {name} {ddl}")
            existing = {r[1] for r in db.execute("PRAGMA table_info(usage_events)")}
            for name, ddl in {"client_id":"TEXT NOT NULL DEFAULT 'cliente_demo_01'", "project":"TEXT NOT NULL DEFAULT 'MantenIA'", "environment":"TEXT NOT NULL DEFAULT 'development'", "component":"TEXT NOT NULL DEFAULT 'backend'", "resource":"TEXT NOT NULL DEFAULT 'cpu'"}.items():
                if name not in existing: db.execute(f"ALTER TABLE usage_events ADD COLUMN {name} {ddl}")

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA secure_delete=ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def register_model(self, info):
        with self.connect() as db:
            db.execute("INSERT OR IGNORE INTO model_info VALUES (?, ?, ?)",
                       (info["version"], json.dumps(info), utcnow()))

    def save_success(self, request_id, kind, result, records, store_raw, rate, client_id='cliente_demo_01', tags=None):
        n = len(result["results"])
        tags = tags or {}
        with self.connect() as db:
            db.execute("INSERT INTO prediction_requests(request_id,timestamp,request_type,record_count,status,total_latency_ms,inference_latency_ms,model_version,error_code,raw_inputs_json,client_id,records_received,records_processed,records_failed,project,environment,component,resource) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (request_id, utcnow(), kind, n, "success", None,
                        result["inference_latency_ms"], result["model_version"], None,
                        json.dumps(records) if store_raw else None, client_id, n, n, 0,
                        tags.get('project','MantenIA'), tags.get('environment','development'), tags.get('component','backend'), tags.get('resource','cpu')))
            db.executemany("INSERT INTO prediction_results VALUES (?, ?, ?, ?)",
                           [(request_id, r["row_index"], r["failure_probability"], r["prediction"]) for r in result["results"]])
            db.execute("INSERT INTO usage_events(request_id,timestamp,billable_units,inference_count,compute_time_ms,cost_rate_mxn,estimated_cost,client_id,project,environment,component,resource) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (request_id, utcnow(), n, n, result["inference_latency_ms"], str(rate), str(rate * n), client_id,
                        tags.get('project','MantenIA'), tags.get('environment','development'), tags.get('component','backend'), tags.get('resource','cpu')))

    def finish(self, request_id, kind, status, latency, error_code=None, client_id='cliente_demo_01'):
        with self.connect() as db:
            row = db.execute("SELECT request_id FROM prediction_requests WHERE request_id=?", (request_id,)).fetchone()
            if row:
                db.execute("UPDATE prediction_requests SET total_latency_ms=? WHERE request_id=?", (latency, request_id))
            else:
                db.execute("INSERT INTO prediction_requests(request_id,timestamp,request_type,record_count,status,total_latency_ms,error_code,client_id,records_received,records_processed,records_failed) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                           (request_id, utcnow(), kind, 0, status, latency, error_code, client_id, 0, 0, 0))

    def billing(self, client_id, start, end, fixed_fee, unit_rate):
        with self.connect() as db:
            row = db.execute("SELECT COUNT(*) requests, COALESCE(SUM(u.billable_units),0) units FROM prediction_requests r LEFT JOIN usage_events u ON u.request_id=r.request_id WHERE r.client_id=? AND r.status='success' AND r.timestamp>=? AND r.timestamp<?", (client_id, start, end)).fetchone()
        units = int(row['units'] or 0)
        return {'client_id':client_id,'period_start':start,'period_end':end,'successful_requests':int(row['requests'] or 0),'billable_units':units,'fixed_fee_mxn':float(fixed_fee),'variable_rate_mxn':float(unit_rate),'variable_charge_mxn':float(unit_rate*units),'total_mxn':float(fixed_fee+unit_rate*units),'currency':'MXN'}

    def history(self, limit=50, offset=0):
        with self.connect() as db:
            return [dict(r) for r in db.execute(
                "SELECT request_id,timestamp,request_type,record_count,status,total_latency_ms,inference_latency_ms,model_version FROM prediction_requests ORDER BY timestamp DESC LIMIT ? OFFSET ?", (limit, offset))]

    def detail(self, request_id):
        with self.connect() as db:
            row = db.execute("SELECT request_id,timestamp,request_type,record_count,status,total_latency_ms,inference_latency_ms,model_version,error_code FROM prediction_requests WHERE request_id=?", (request_id,)).fetchone()
            if row is None:
                return None
            result = dict(row)
            result["results"] = [dict(r) for r in db.execute(
                "SELECT row_index,failure_probability,prediction FROM prediction_results WHERE request_id=? ORDER BY failure_probability DESC,row_index", (request_id,))]
            return result

    def snapshot(self):
        with self.connect() as db:
            requests = [dict(r) for r in db.execute("SELECT request_type,status,total_latency_ms,inference_latency_ms,record_count FROM prediction_requests")]
            events = [dict(r) for r in db.execute("SELECT u.*,r.request_type FROM usage_events u JOIN prediction_requests r USING(request_id)")]
        return requests, events

    def purge(self, days):
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        with self.connect() as db:
            count = db.execute("DELETE FROM prediction_requests WHERE timestamp < ?", (cutoff,)).rowcount
        with self.connect() as db:
            db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        return count
