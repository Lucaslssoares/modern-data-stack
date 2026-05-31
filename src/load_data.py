import pandas as pd

from common.database import get_engine
from common.logger import get_logger

log = get_logger(__name__)


def load_data(
    table_name: str,
    df: pd.DataFrame,
    if_exists: str = "append",
) -> None:
    """
    Carrega o DataFrame no PostgreSQL.

    Parâmetros
    ----------
    table_name : tabela de destino (definida em pipeline_config.TABLE_NAME)
    df         : DataFrame transformado
    if_exists  : "append" acumula | "replace" recria a tabela a cada carga
    """
    engine = get_engine()
    df.to_sql(name=table_name, con=engine, if_exists=if_exists, index=False)

    with engine.connect() as conn:
        total = conn.execute(
            __import__("sqlalchemy").text(f"SELECT COUNT(*) FROM {table_name}")
        ).scalar()

    log.info("Carga concluída — total de registros em '%s': %d", table_name, total)
