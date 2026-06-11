"""
Backfill histórico — Open-Meteo Archive API
============================================
Busca dados meteorológicos horários para múltiplos municípios da região
dendezeira do NE do Pará e carrega em bronze.raw_openmeteo.

Uso:
    python scripts/backfill_historico.py                              # todos os municípios, últimos 2 anos
    python scripts/backfill_historico.py --localidades tailandia,acara,moju
    python scripts/backfill_historico.py 2023-01-01                   # desde 01/01/2023
    python scripts/backfill_historico.py 2022-01-01 2024-12-31
"""
import sys
import json
import time
import argparse
import logging
from datetime import date, timedelta
from pathlib import Path
from dateutil.relativedelta import relativedelta

import requests
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("backfill")

_ENV_PATH = Path(__file__).resolve().parent.parent / "config" / ".env"
load_dotenv(_ENV_PATH)

DB_USER     = os.getenv("DB_USER",     "airflow")
DB_PASSWORD = os.getenv("DB_PASSWORD", "airflow")
DB_HOST     = os.getenv("DB_HOST",     "localhost")
DB_PORT     = os.getenv("DB_PORT",     "5432")
DB_NAME     = os.getenv("DB_NAME",     "airflow")

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
TIMEZONE    = "America/Belem"
VARIABLES   = ",".join([
    "temperature_2m",
    "apparent_temperature",
    "relativehumidity_2m",
    "dewpoint_2m",
    "precipitation",
    "windspeed_10m",
    "windgusts_10m",
    "winddirection_10m",
    "pressure_msl",
    "shortwave_radiation",
])

LOCATIONS = [
    {"nome": "tome_acu",  "label": "Tomé-Açu",  "latitude": -2.42, "longitude": -48.15},
    {"nome": "tailandia", "label": "Tailândia",  "latitude": -2.93, "longitude": -48.95},
    {"nome": "acara",     "label": "Acará",      "latitude": -1.96, "longitude": -48.20},
    {"nome": "moju",      "label": "Moju",       "latitude": -1.88, "longitude": -48.77},
]

BRONZE_SCHEMA = "bronze"
BRONZE_TABLE  = "raw_openmeteo"


def get_engine():
    url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url)


def ensure_schema(engine):
    with engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {BRONZE_SCHEMA}"))
        conn.commit()


def fetch_chunk(loc: dict, start: date, end: date) -> pd.DataFrame:
    params = {
        "latitude":        loc["latitude"],
        "longitude":       loc["longitude"],
        "start_date":      start.strftime("%Y-%m-%d"),
        "end_date":        end.strftime("%Y-%m-%d"),
        "hourly":          VARIABLES,
        "timezone":        TIMEZONE,
        "wind_speed_unit": "ms",
    }
    resp = requests.get(ARCHIVE_URL, params=params, timeout=60)
    resp.raise_for_status()

    data = resp.json()
    hourly = data.get("hourly", {})
    df = pd.DataFrame(hourly)

    for key in ("latitude", "longitude", "elevation", "timezone"):
        if key in data:
            df[key] = data[key]

    df["_loaded_at"] = pd.Timestamp.now(tz="UTC")
    df["_source"]    = f"openmeteo_{loc['nome']}_backfill"

    return df


def load_chunk(engine, df: pd.DataFrame):
    df.to_sql(
        name=BRONZE_TABLE,
        con=engine,
        schema=BRONZE_SCHEMA,
        if_exists="append",
        index=False,
    )


def count_rows(engine) -> int:
    with engine.connect() as conn:
        return conn.execute(
            text(f"SELECT COUNT(*) FROM {BRONZE_SCHEMA}.{BRONZE_TABLE}")
        ).scalar()


def build_chunks(data_inicio: date, data_fim: date):
    chunks = []
    cursor = data_inicio
    while cursor <= data_fim:
        fim_mes = min(cursor + relativedelta(months=1) - timedelta(days=1), data_fim)
        chunks.append((cursor, fim_mes))
        cursor = fim_mes + timedelta(days=1)
    return chunks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("data_inicio", nargs="?", help="YYYY-MM-DD (padrão: 2 anos atrás)")
    parser.add_argument("data_fim",    nargs="?", help="YYYY-MM-DD (padrão: ontem)")
    parser.add_argument(
        "--localidades",
        help="Nomes separados por vírgula: tome_acu,tailandia,acara,moju",
        default=None,
    )
    args = parser.parse_args()

    hoje  = date.today()
    ontem = hoje - timedelta(days=1)

    data_inicio = date.fromisoformat(args.data_inicio) if args.data_inicio else ontem - relativedelta(years=2)
    data_fim    = date.fromisoformat(args.data_fim)    if args.data_fim    else ontem

    if args.localidades:
        filtro = {n.strip() for n in args.localidades.split(",")}
        locs = [l for l in LOCATIONS if l["nome"] in filtro]
        nao_encontrados = filtro - {l["nome"] for l in locs}
        if nao_encontrados:
            log.warning("Localidades desconhecidas ignoradas: %s", nao_encontrados)
    else:
        locs = LOCATIONS

    log.info("Localidades: %s", [l["label"] for l in locs])
    log.info("Período:     %s → %s", data_inicio, data_fim)

    engine = get_engine()
    ensure_schema(engine)

    chunks = build_chunks(data_inicio, data_fim)
    log.info("%d chunk(s) mensais × %d localidade(s) = %d requests",
             len(chunks), len(locs), len(chunks) * len(locs))

    total_linhas = 0
    for loc in locs:
        log.info("=== %s (lat=%.2f lon=%.2f) ===", loc["label"], loc["latitude"], loc["longitude"])
        for i, (inicio, fim) in enumerate(chunks, 1):
            log.info("  [%d/%d] %s → %s ...", i, len(chunks), inicio, fim)
            try:
                df = fetch_chunk(loc, inicio, fim)
                load_chunk(engine, df)
                total_linhas += len(df)
                log.info("         ✓ %d linhas", len(df))
            except Exception as exc:
                log.error("         ✗ Erro: %s", exc)
            if i < len(chunks):
                time.sleep(0.5)
        time.sleep(1)

    total_db = count_rows(engine)
    log.info("Backfill concluído — %d linhas novas | %d total em bronze.%s",
             total_linhas, total_db, BRONZE_TABLE)


if __name__ == "__main__":
    main()
