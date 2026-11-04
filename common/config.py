import os
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=False)

@dataclass(frozen=True)
class Settings:
    edge_url: str = os.getenv("EDGE_SERVICE_URL", "http://127.0.0.1:8001")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///database/mantenia.db")
    store_raw: bool = os.getenv("STORE_RAW_INPUTS", "false").lower() == "true"
    cost_rate: Decimal = Decimal(os.getenv("ESTIMATED_COST_PER_INFERENCE_MXN", "0.7333"))
    billing_fixed_fee: Decimal = Decimal(os.getenv("BILLING_FIXED_FEE_MXN", "3500.00"))
    billing_rate: Decimal = Decimal(os.getenv("BILLING_RATE_PER_UNIT_MXN", "1.00"))
    project: str = os.getenv("PROJECT_NAME", "MantenIA")
    environment: str = os.getenv("APP_ENV", "development")
    component: str = os.getenv("COMPONENT_NAME", "backend")
    resource: str = os.getenv("RESOURCE_NAME", "cpu")
    default_client_id: str = os.getenv("DEFAULT_CLIENT_ID", "cliente_demo_01")
    max_rows: int = int(os.getenv("MAX_CSV_ROWS", "1000"))
    max_bytes: int = int(os.getenv("MAX_REQUEST_BYTES", "2097152"))
    retention_days: int = int(os.getenv("RETENTION_DAYS", "30"))
    edge_timeout: float = float(os.getenv("EDGE_TIMEOUT_SECONDS", "30"))
    model_dir: Path = Path(os.getenv("MODEL_DIR", str(ROOT / "edge_service/models")))

    def __post_init__(self):
        target = urlparse(self.edge_url)
        if target.scheme != "http" or target.hostname not in {"edge", "localhost", "127.0.0.1", "::1"} or target.username:
            raise ValueError("EDGE_SERVICE_URL debe apuntar al servicio local edge o localhost")
        if not self.cost_rate.is_finite() or self.cost_rate < 0 or self.billing_fixed_fee < 0 or self.billing_rate < 0:
            raise ValueError("Costo unitario inválido")
        if not 1 <= self.max_rows <= 100000 or self.max_bytes < 1024 or self.retention_days < 1:
            raise ValueError("Límites de configuración inválidos")
        if not self.database_url.startswith("sqlite:///"):
            raise ValueError("Solo se permite SQLite local")

    @property
    def database_path(self):
        path = Path(self.database_url.removeprefix("sqlite:///"))
        return path if path.is_absolute() else ROOT / path
