import sys
import os
from datetime import datetime, timedelta
from airflow.decorators import dag, task

sys.path.insert(0, '/opt/airflow/src')
sys.path.insert(0, '/opt/airflow/config')

from extract_data import extract_data
from transform_data import data_transformation_pipeline
from load_data import load_data
import pipeline_config as cfg


@dag(
    dag_id=cfg.DAG_ID,
    default_args={
        'owner': cfg.DAG_OWNER,
        'depends_on_past': False,
        'retries': 2,
        'retry_delay': timedelta(minutes=5),
    },
    description=cfg.DAG_DESCRIPTION,
    schedule=cfg.DAG_SCHEDULE,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=cfg.DAG_TAGS,
)
def etl_pipeline():

    @task
    def extract():
        from dotenv import load_dotenv
        load_dotenv('/opt/airflow/config/.env')
        api_key = os.getenv('API_KEY')
        if not api_key:
            raise ValueError("API_KEY não encontrada no .env")
        url = cfg.API_BASE_URL.format(api_key=api_key)
        extract_data(url, output_path=cfg.RAW_DATA_PATH)

    @task
    def transform():
        os.makedirs('/opt/airflow/data', exist_ok=True)
        df = data_transformation_pipeline(raw_path=cfg.RAW_DATA_PATH)
        df.to_parquet(cfg.TEMP_DATA_PATH, index=False)

    @task
    def load():
        import pandas as pd
        df = pd.read_parquet(cfg.TEMP_DATA_PATH)
        load_data(cfg.TABLE_NAME, df)

    extract() >> transform() >> load()


etl_pipeline()
