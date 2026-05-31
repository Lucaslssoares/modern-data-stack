"""Execução local do pipeline ELT (fora do Airflow/Docker)."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "config"))

from dotenv import load_dotenv
load_dotenv(ROOT / "config" / ".env")

from extract_data import extract_data          # noqa: E402
from flatten_data import flatten_to_bronze     # noqa: E402
from load_data import load_data                # noqa: E402
import pipeline_config as cfg                  # noqa: E402
from common.logger import get_logger           # noqa: E402

log = get_logger("pipeline")

# Caminhos locais (sem /opt/airflow)
RAW = str(ROOT / "data" / "raw_data.json")


def run():
    api_key = os.getenv("API_KEY")
    if not api_key:
        raise ValueError("API_KEY não definida em config/.env")

    url = cfg.API_BASE_URL.format(api_key=api_key)

    log.info("=== EXTRACT ===")
    extract_data(url, output_path=RAW)

    log.info("=== LOAD BRONZE ===")
    df = flatten_to_bronze(RAW)
    load_data(cfg.BRONZE_TABLE, df, schema=cfg.BRONZE_SCHEMA)

    log.info("=== dbt SILVER + GOLD — execute manualmente: ===")
    log.info("docker exec airflow-weather-pipeline-dbt-1 dbt run")


if __name__ == "__main__":
    run()
