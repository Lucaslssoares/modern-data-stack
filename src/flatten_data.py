import json
from pathlib import Path

import pandas as pd

from common.logger import get_logger

log = get_logger(__name__)


def flatten_to_bronze(raw_path: str, source_name: str = "openmeteo") -> pd.DataFrame:
    """
    Lê o JSON bruto da Open-Meteo e normaliza para a camada Bronze.

    A Open-Meteo retorna formato COLUMNAR:
      {"hourly": {"time": [...], "temperature_2m": [...], ...}}

    Este função converte para formato TABULAR (1 linha por hora).

    Parâmetros
    ----------
    raw_path    : caminho para o arquivo JSON gerado pelo Extract
    source_name : identificador da fonte (gravado em _source)
    """
    path = Path(raw_path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {raw_path}")

    data = json.loads(path.read_text(encoding="utf-8"))

    # Converte colunas horárias em linhas
    hourly = data.get("hourly", {})
    df = pd.DataFrame(hourly)

    # Metadados do ponto geográfico (igual para todas as linhas)
    for key in ("latitude", "longitude", "elevation", "timezone"):
        if key in data:
            df[key] = data[key]

    df["_loaded_at"] = pd.Timestamp.now(tz="UTC")
    df["_source"]    = source_name

    log.info("Bronze pronto — %d linha(s), %d colunas", len(df), len(df.columns))
    return df
