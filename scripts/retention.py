from common.config import Settings
from backend.app.database import Database
if __name__ == "__main__":
    settings = Settings()
    print("Operaciones vencidas eliminadas:", Database(settings.database_path).purge(settings.retention_days))
