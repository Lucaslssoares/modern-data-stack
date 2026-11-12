"""API de consulta à camada Gold — aplicação usada no CI/CD, Kubernetes e Elastic."""
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from urllib.parse import quote_plus

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text

SERVICE_NAME = "clima-api"
VERSION = os.getenv("APP_VERSION", "dev")


# ── Logs em JSON (uma linha por evento) — o Filebeat decodifica sem parser extra ──
class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        doc = {
            "@timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "log.level": record.levelname.lower(),
            "message": record.getMessage(),
            "service.name": SERVICE_NAME,
            "service.version": VERSION,
        }
        doc.update(getattr(record, "fields", {}))
        return json.dumps(doc, ensure_ascii=False)


handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
log = logging.getLogger(SERVICE_NAME)
log.handlers = [handler]
log.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
log.propagate = False


# ── Banco (mesmas variáveis DB_* do pipeline) ──────────────────────────────────
_engine = None


def get_engine():
    global _engine
    if _engine is None:
        url = "postgresql+psycopg2://{u}:{p}@{h}:{port}/{db}".format(
            u=os.getenv("DB_USER", "airflow"),
            p=quote_plus(os.getenv("DB_PASSWORD", "airflow")),
            h=os.getenv("DB_HOST", "postgres"),
            port=os.getenv("DB_PORT", "5432"),
            db=os.getenv("DB_NAME", "airflow"),
        )
        _engine = create_engine(url, pool_pre_ping=True)
    return _engine


def run_query(sql: str, params: dict) -> list[dict]:
    with get_engine().connect() as conn:
        return [dict(r._mapping) for r in conn.execute(text(sql), params)]


def get_query():
    return run_query


# Compara localidade sem acento/caixa: "moju", "tome_acu" ou "Tomé-Açu" casam com o rótulo da gold
_SLUG = "translate(lower({}), 'áàâãéêíóôõúç- ', 'aaaaeeiooouc__')"
FILTRO_LOCALIDADE = f"(:loc is null or {_SLUG.format('nome_localidade')} = {_SLUG.format(':loc')})"

app = FastAPI(title="Clima API", version=VERSION)


@app.middleware("http")
async def access_log(request: Request, call_next):
    start = time.perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    except Exception as exc:
        # Erro não tratado vira uma única linha JSON (sem traceback multilinha no Filebeat)
        log.error("Erro não tratado: %r", exc, extra={"fields": {"error.type": type(exc).__name__}})
        return JSONResponse({"detail": "Erro interno"}, status_code=500)
    finally:
        ms = round((time.perf_counter() - start) * 1000, 2)
        log.info(
            "%s %s %s", request.method, request.url.path, status,
            extra={"fields": {
                "http.request.method": request.method,
                "url.path": request.url.path,
                "http.response.status_code": status,
                "http.response.duration_ms": ms,
            }},
        )


@app.get("/health")
def health():
    return {"status": "ok", "version": VERSION}


@app.get("/clima/diario")
def clima_diario(localidade: str | None = None, limite: int = 30, query=Depends(get_query)):
    sql = f"""
        select nome_localidade, data_medicao, temperatura_media_c, temperatura_max_c,
               temperatura_min_c, chuva_total_mm, umidade_media_pct
        from gold.fct_clima_diario
        where {FILTRO_LOCALIDADE}
        order by data_medicao desc
        limit :lim
    """
    try:
        rows = query(sql, {"loc": localidade, "lim": min(limite, 500)})
    except Exception as exc:
        log.error("Falha ao consultar gold.fct_clima_diario: %s", exc)
        raise HTTPException(status_code=503, detail="Banco indisponível")
    if localidade and not rows:
        raise HTTPException(status_code=404, detail=f"Localidade '{localidade}' sem dados")
    return rows


@app.get("/clima/mensal")
def clima_mensal(localidade: str | None = None, query=Depends(get_query)):
    sql = f"""
        select nome_localidade, mes, chuva_total_mm, chuva_acum_3m_mm,
               balanco_hidrico_mm, status_hidrico
        from gold.fct_clima_mensal
        where {FILTRO_LOCALIDADE}
        order by nome_localidade, mes desc
    """
    try:
        return query(sql, {"loc": localidade})
    except Exception as exc:
        log.error("Falha ao consultar gold.fct_clima_mensal: %s", exc)
        raise HTTPException(status_code=503, detail="Banco indisponível")


@app.get("/simular-erro")
def simular_erro():
    """Gera um 500 de propósito — útil para demonstrar erros no dashboard."""
    raise RuntimeError("erro simulado")
