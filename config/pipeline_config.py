import os
from pathlib import Path

# Raiz do projeto — funciona em Docker (/opt/airflow) e localmente
BASE_DIR = Path(os.getenv("AIRFLOW_HOME", Path(__file__).resolve().parent.parent))

# =============================================================================
# DAG
# =============================================================================
DAG_ID          = "openmeteo_pipeline"
DAG_DESCRIPTION = "Pipeline ELT — dados meteorológicos Open-Meteo (ERA5/ICON)"
DAG_SCHEDULE    = "0 6 * * *"   # todo dia às 06h — garante D-1 completo
DAG_OWNER       = "admin"
DAG_TAGS        = ["elt", "medallion", "openmeteo", "meteorologia"]

# =============================================================================
# Open-Meteo API — https://open-meteo.com  (gratuita, sem token)
# Endpoint forecast : dados recentes + passado recente (últimos 7 dias)
# Endpoint archive  : dados históricos (qualquer data desde 1940)
# =============================================================================
OPENMETEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
OPENMETEO_ARCHIVE_URL  = "https://archive-api.open-meteo.com/v1/archive"

# Municípios da região dendezeira do NE do Pará
LOCATIONS = [
    {"nome": "tome_acu",  "label": "Tomé-Açu",  "latitude": -2.42, "longitude": -48.15},
    {"nome": "tailandia", "label": "Tailândia",  "latitude": -2.93, "longitude": -48.95},
    {"nome": "acara",     "label": "Acará",      "latitude": -1.96, "longitude": -48.20},
    {"nome": "moju",      "label": "Moju",       "latitude": -1.88, "longitude": -48.77},
]

OPENMETEO_TIMEZONE  = "America/Belem"

# Variáveis meteorológicas coletadas
OPENMETEO_VARIABLES = ",".join([
    "temperature_2m",        # temperatura a 2m (°C)
    "apparent_temperature",  # temperatura de sensação (°C)
    "relativehumidity_2m",   # umidade relativa a 2m (%)
    "dewpoint_2m",           # ponto de orvalho (°C)
    "precipitation",         # precipitação (mm)
    "windspeed_10m",         # velocidade do vento a 10m (m/s)
    "windgusts_10m",         # rajada do vento a 10m (m/s)
    "winddirection_10m",     # direção do vento (graus)
    "pressure_msl",          # pressão ao nível do mar (hPa = mbar)
    "shortwave_radiation",   # radiação solar de ondas curtas (W/m²)
])

# =============================================================================
# Camadas Medallion
# =============================================================================
BRONZE_SCHEMA = "bronze"
SILVER_SCHEMA = "silver"
GOLD_SCHEMA   = "gold"

BRONZE_TABLE  = "raw_openmeteo"

# =============================================================================
# Caminhos
# =============================================================================
DATA_DIR      = BASE_DIR / "data"
RAW_DATA_PATH = str(DATA_DIR / "raw_openmeteo.json")
