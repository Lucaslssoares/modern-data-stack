import os
import sys
from datetime import datetime, timedelta

from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator

sys.path.insert(0, "/opt/airflow/src")
sys.path.insert(0, "/opt/airflow/config")

from extract_data import extract_data          # noqa: E402
from flatten_data import flatten_to_bronze     # noqa: E402
from load_data import load_data                # noqa: E402
import pipeline_config as cfg                  # noqa: E402

_DBT_CMD = (
    "dbt run "
    "--project-dir /opt/airflow/dbt "
    "--profiles-dir /opt/airflow/config/dbt "
    "--select {layer}"
)

_DBT_TEST_CMD = (
    "dbt test "
    "--project-dir /opt/airflow/dbt "
    "--profiles-dir /opt/airflow/config/dbt "
    "--select {layer}"
)


@dag(
    dag_id=cfg.DAG_ID,
    default_args={
        "owner": cfg.DAG_OWNER,
        "depends_on_past": False,
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
    },
    description=cfg.DAG_DESCRIPTION,
    schedule=cfg.DAG_SCHEDULE,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=cfg.DAG_TAGS,
)
def medallion_pipeline():
    """
    Pipeline ELT com arquitetura Medallion — dados Open-Meteo (ERA5/ICON).

    Fluxo:
        extract → bronze (Python) → silver (dbt) → gold (dbt)

    Camadas:
        Bronze : dados brutos da API Open-Meteo, sem transformação
        Silver : dados limpos, tipados e padronizados (dbt views)
        Gold   : métricas diárias e mensais para análise (dbt tables)
    """

    # ── EXTRACT ──────────────────────────────────────────────────────────────
    @task
    def extract():
        import time
        from datetime import date, timedelta

        hoje  = date.today()
        ontem = hoje - timedelta(days=1)

        for i, loc in enumerate(cfg.LOCATIONS):
            url = (
                f"{cfg.OPENMETEO_ARCHIVE_URL}"
                f"?latitude={loc['latitude']}"
                f"&longitude={loc['longitude']}"
                f"&start_date={ontem.strftime('%Y-%m-%d')}"
                f"&end_date={hoje.strftime('%Y-%m-%d')}"
                f"&hourly={cfg.OPENMETEO_VARIABLES}"
                f"&timezone={cfg.OPENMETEO_TIMEZONE}"
                f"&wind_speed_unit=ms"
            )
            output_path = str(cfg.DATA_DIR / f"raw_openmeteo_{loc['nome']}.json")
            extract_data(url, output_path=output_path)
            if i < len(cfg.LOCATIONS) - 1:
                time.sleep(1)

    # ── BRONZE (Load) ─────────────────────────────────────────────────────────
    @task
    def load_bronze():
        import pandas as pd

        dfs = []
        for loc in cfg.LOCATIONS:
            raw_path = str(cfg.DATA_DIR / f"raw_openmeteo_{loc['nome']}.json")
            df = flatten_to_bronze(raw_path, source_name=f"openmeteo_{loc['nome']}")
            dfs.append(df)
        df_all = pd.concat(dfs, ignore_index=True)
        load_data(cfg.BRONZE_TABLE, df_all, schema=cfg.BRONZE_SCHEMA)

    # ── SILVER (dbt) ─────────────────────────────────────────────────────────
    dbt_silver = BashOperator(
        task_id="dbt_silver",
        bash_command=_DBT_CMD.format(layer="silver"),
    )

    dbt_test_silver = BashOperator(
        task_id="dbt_test_silver",
        bash_command=_DBT_TEST_CMD.format(layer="silver"),
    )

    # ── GOLD (dbt) ───────────────────────────────────────────────────────────
    dbt_gold = BashOperator(
        task_id="dbt_gold",
        bash_command=_DBT_CMD.format(layer="gold"),
    )

    dbt_test_gold = BashOperator(
        task_id="dbt_test_gold",
        bash_command=_DBT_TEST_CMD.format(layer="gold"),
    )

    # ── FLUXO ────────────────────────────────────────────────────────────────
    (
        extract()
        >> load_bronze()
        >> dbt_silver
        >> dbt_test_silver
        >> dbt_gold
        >> dbt_test_gold
    )


medallion_pipeline()
