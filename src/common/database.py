import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from common.logger import get_logger

log = get_logger(__name__)

_ENV_PATH = os.path.join(
    os.getenv("AIRFLOW_HOME", os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "config", ".env",
)


def get_engine() -> Engine:
    load_dotenv(_ENV_PATH)

    user     = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    database = os.getenv("DB_NAME")
    host     = os.getenv("DB_HOST", "postgres")
    port     = os.getenv("DB_PORT", "5432")

    if not all([user, password, database]):
        raise EnvironmentError("Credenciais DB_USER / DB_PASSWORD / DB_NAME não definidas no .env")

    url = f"postgresql+psycopg2://{user}:{quote_plus(password)}@{host}:{port}/{database}"
    log.info("Conectando em %s:%s/%s", host, port, database)
    return create_engine(url, pool_pre_ping=True)
