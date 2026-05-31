import json
import os
import sys
from pathlib import Path

import pandas as pd

from common.logger import get_logger

log = get_logger(__name__)

# Garante que pipeline_config seja encontrado tanto no Airflow quanto localmente
_cfg_dir = os.path.join(
    os.getenv("AIRFLOW_HOME", str(Path(__file__).resolve().parents[1])),
    "config",
)
if _cfg_dir not in sys.path:
    sys.path.insert(0, _cfg_dir)

import pipeline_config as cfg  # noqa: E402


def create_dataframe(raw_path: str) -> pd.DataFrame:
    """Carrega o JSON bruto e aplana objetos aninhados com json_normalize."""
    path = Path(raw_path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {raw_path}")

    data = json.loads(path.read_text(encoding="utf-8"))

    # -------------------------------------------------------------------------
    # AJUSTE AQUI conforme a estrutura da sua API:
    #   Objeto único:           pd.json_normalize(data)
    #   Lista de registros:     pd.json_normalize(data, record_path="items")
    # -------------------------------------------------------------------------
    df = pd.json_normalize(data)
    log.info("DataFrame criado — %d linhas, %d colunas", len(df), len(df.columns))
    return df


def normalize_nested_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Expande colunas com listas ou dicionários aninhados.

    AJUSTE AQUI: adicione normalização específica da sua API.

    Exemplo:
        nested = pd.json_normalize(df["eventos"].apply(lambda x: x[0]))
        df = pd.concat([df, nested], axis=1)
    """
    return df


def drop_columns(df: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in cfg.COLUMNS_TO_DROP if c in df.columns]
    if cols:
        df = df.drop(columns=cols)
        log.info("Colunas removidas: %s", cols)
    return df


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns=cfg.COLUMNS_TO_RENAME)
    if cfg.COLUMNS_TO_RENAME:
        log.info("Colunas renomeadas: %d mapeamentos aplicados", len(cfg.COLUMNS_TO_RENAME))
    return df


def convert_datetime_columns(df: pd.DataFrame) -> pd.DataFrame:
    for col in cfg.DATETIME_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], unit="s", utc=True).dt.tz_convert(cfg.TIMEZONE)
            log.info("Coluna '%s' convertida para datetime (%s)", col, cfg.TIMEZONE)
    return df


def custom_transformations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transformações específicas do domínio.

    AJUSTE AQUI: cálculos derivados, filtros, tipagens, tratamento de nulos.

    Exemplos:
        df["valor_brl"] = df["valor_usd"] * taxa_cambio
        df = df[df["status"] == "ativo"]
    """
    return df


def data_transformation_pipeline(raw_path: str) -> pd.DataFrame:
    log.info("Iniciando transformação...")
    df = create_dataframe(raw_path)
    df = normalize_nested_columns(df)
    df = drop_columns(df)
    df = rename_columns(df)
    df = convert_datetime_columns(df)
    df = custom_transformations(df)
    log.info("Transformação concluída — shape final: %s", df.shape)
    return df
