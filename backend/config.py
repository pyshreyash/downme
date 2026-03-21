from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
import dotenv, os

dotenv.load_dotenv(Path(__file__).parent / ".env")


@dataclass
class Settings:
    secret_key: str = os.getenv("SECRET_KEY")
    algorithm: str = os.getenv("ALGORITHM")
    session_timeout: timedelta = timedelta(minutes=int(os.getenv("SESSION_TIMEOUT_MINUTES", 60)))
    database_url: str = os.getenv("DATABASE_URL")

    azure_account_name: str = os.getenv("AZURE_ACCOUNT_NAME")
    azure_account_key: str = os.getenv("AZURE_ACCOUNT_KEY")
    azure_blob_endpoint: str = os.getenv("AZURE_BLOB_ENDPOINT")
    azure_conn_string: str = os.getenv("AZURE_CONN_STRING")

    upload_sas_minutes: int = 60*3
    download_sas_minutes: int = 60*3
    chunk_size_bytes: int = 2 * 1024 * 1024 # 2MB

settings = Settings()

    