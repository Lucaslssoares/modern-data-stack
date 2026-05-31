import os
from pathlib import Path

# Raiz do projeto — funciona em Docker (/opt/airflow) e localmente
BASE_DIR = Path(os.getenv("AIRFLOW_HOME", Path(__file__).resolve().parent.parent))

# =============================================================================
# DAG
# =============================================================================
DAG_ID          = "meu_pipeline_elt"
DAG_DESCRIPTION = "Pipeline ELT Medallion — <tema>"
DAG_SCHEDULE    = "0 */1 * * *"
DAG_OWNER       = "admin"
DAG_TAGS        = ["elt", "medallion"]

# =============================================================================
# API — fonte de dados
# =============================================================================
API_BASE_URL = "https://api.exemplo.com/endpoint?appid={api_key}"

# =============================================================================
# Camadas Medallion
# =============================================================================
BRONZE_SCHEMA = "bronze"   # raw — carregado pelo Airflow (Python)
SILVER_SCHEMA = "silver"   # clean — transformado pelo dbt
GOLD_SCHEMA   = "gold"     # business — agregado pelo dbt

BRONZE_TABLE  = "raw_source"   # renomear para raw_<tema> ao definir o tema

# =============================================================================
# Caminhos
# =============================================================================
DATA_DIR      = BASE_DIR / "data"
RAW_DATA_PATH = str(DATA_DIR / "raw_data.json")
