import os
from pathlib import Path

# Resolve raiz do projeto:
#   - Em Docker/Airflow: AIRFLOW_HOME=/opt/airflow
#   - Localmente: pasta pai deste arquivo (project root)
BASE_DIR = Path(os.getenv("AIRFLOW_HOME", Path(__file__).resolve().parent.parent))

# =============================================================================
# DAG
# =============================================================================
DAG_ID          = "meu_pipeline_etl"
DAG_DESCRIPTION = "Pipeline ETL - <tema>"
DAG_SCHEDULE    = "0 */1 * * *"     # a cada 1h | "@daily" | "@hourly"
DAG_OWNER       = "admin"
DAG_TAGS        = ["etl"]

# =============================================================================
# API
# =============================================================================
# URL da fonte de dados. {api_key} é substituído em runtime com o valor do .env
API_BASE_URL = "https://api.exemplo.com/endpoint?param=valor&appid={api_key}"

# =============================================================================
# Banco de dados — destino final dos dados carregados
# =============================================================================
TABLE_NAME = "minha_tabela"

# =============================================================================
# Caminhos de dados intermediários
# =============================================================================
DATA_DIR       = BASE_DIR / "data"
RAW_DATA_PATH  = str(DATA_DIR / "raw_data.json")
TEMP_DATA_PATH = str(DATA_DIR / "temp_data.parquet")

# =============================================================================
# Transform — mapeamento de colunas
# =============================================================================
COLUMNS_TO_DROP: list[str] = [
    # "coluna_a",
]

COLUMNS_TO_RENAME: dict[str, str] = {
    # "nome_api": "nome_padronizado",
}

DATETIME_COLUMNS: list[str] = [
    # "datetime",
]

TIMEZONE = "America/Sao_Paulo"
