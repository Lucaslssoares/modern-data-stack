"""Execução local do pipeline (fora do Airflow/Docker)."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "config"))

from dotenv import load_dotenv

load_dotenv(ROOT / "config" / ".env")

from extract_data import extract_data              # noqa: E402
from transform_data import data_transformation_pipeline  # noqa: E402
from load_data import load_data                    # noqa: E402
import pipeline_config as cfg                      # noqa: E402
from common.logger import get_logger               # noqa: E402

log = get_logger("pipeline")

# Sobrescreve os paths do config para rodar localmente (sem /opt/airflow)
RAW  = str(ROOT / "data" / "raw_data.json")
TEMP = str(ROOT / "data" / "temp_data.parquet")


def run():
    api_key = os.getenv("API_KEY")
    if not api_key:
        raise ValueError("API_KEY não definida em config/.env")

    url = cfg.API_BASE_URL.format(api_key=api_key)

    log.info("=== ETAPA 1: EXTRACT ===")
    extract_data(url, output_path=RAW)

    log.info("=== ETAPA 2: TRANSFORM ===")
    df = data_transformation_pipeline(raw_path=RAW)
    df.to_parquet(TEMP, index=False)

    log.info("=== ETAPA 3: LOAD ===")
    load_data(cfg.TABLE_NAME, df)

    log.info("Pipeline concluído com sucesso.")


if __name__ == "__main__":
    run()
