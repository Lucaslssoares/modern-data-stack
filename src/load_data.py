import pandas as pd
from sqlalchemy import text

from common.database import get_engine
from common.logger import get_logger

log = get_logger(__name__)


def _ensure_schema(schema: str) -> None:
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        conn.commit()
    log.info("Schema '%s' verificado.", schema)


def load_data(
    table_name: str,
    df: pd.DataFrame,
    schema: str = "bronze",
    if_exists: str = "append",
) -> None:
    """
    Carrega o DataFrame no schema e tabela especificados.

    Parâmetros
    ----------
    table_name : nome da tabela de destino (ex: pipeline_config.BRONZE_TABLE)
    df         : DataFrame com dados + metadados _loaded_at / _source
    schema     : schema PostgreSQL ('bronze', 'silver', 'gold')
    if_exists  : 'append' acumula | 'replace' recria a tabela
    """
    _ensure_schema(schema)
    engine = get_engine()

    df.to_sql(name=table_name, con=engine, schema=schema, if_exists=if_exists, index=False)

    with engine.connect() as conn:
        total = conn.execute(
            text(f"SELECT COUNT(*) FROM {schema}.{table_name}")
        ).scalar()

    log.info("Carga concluída — %d registros em '%s.%s'", total, schema, table_name)
