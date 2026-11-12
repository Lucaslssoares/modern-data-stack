import io
import json
from datetime import date

import pytest
from fastapi.testclient import TestClient

from clima_api.main import app, get_query, handler


@pytest.fixture
def client():
    def fake_query(sql, params):
        rows = [
            {"nome_localidade": "moju", "data_medicao": date(2026, 1, 1), "chuva_total_mm": 12.5},
            {"nome_localidade": "acara", "data_medicao": date(2026, 1, 1), "chuva_total_mm": 3.0},
        ]
        return [r for r in rows if params["loc"] in (None, r["nome_localidade"])]

    app.dependency_overrides[get_query] = lambda: fake_query
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_diario_filtra_localidade(client):
    resp = client.get("/clima/diario", params={"localidade": "moju"})
    assert resp.status_code == 200
    assert [r["nome_localidade"] for r in resp.json()] == ["moju"]


def test_diario_localidade_inexistente_retorna_404(client):
    assert client.get("/clima/diario", params={"localidade": "belem"}).status_code == 404


def test_banco_indisponivel_retorna_503():
    def broken(sql, params):
        raise ConnectionError("sem conexão")

    app.dependency_overrides[get_query] = lambda: broken
    try:
        assert TestClient(app).get("/clima/mensal").status_code == 503
    finally:
        app.dependency_overrides.clear()


def test_access_log_em_json(client):
    buffer = io.StringIO()
    stream = handler.setStream(buffer)
    try:
        client.get("/simular-erro")
    finally:
        handler.setStream(stream)
    linha = buffer.getvalue().strip().splitlines()[-1]
    doc = json.loads(linha)
    assert doc["http.response.status_code"] == 500
    assert doc["url.path"] == "/simular-erro"
    assert "http.response.duration_ms" in doc
