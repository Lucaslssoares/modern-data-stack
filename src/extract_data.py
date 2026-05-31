import json
from pathlib import Path

import requests

from common.logger import get_logger

log = get_logger(__name__)


def extract_data(url: str, output_path: str = "data/raw_data.json") -> dict:
    """
    GET na URL e salva JSON bruto em output_path.

    AJUSTE AQUI se a API exigir:
      - Header de autenticação:  headers = {"Authorization": f"Bearer {token}"}
      - POST:                    requests.post(url, json={...})
      - Paginação:               loop com offset/cursor
    """
    log.info("Extraindo dados de: %s", url.split("?")[0])

    response = requests.get(url, timeout=30)

    if response.status_code != 200:
        log.error("Erro HTTP %s: %s", response.status_code, response.text[:200])
        raise RuntimeError(f"Falha na extração: HTTP {response.status_code}")

    data = response.json()
    if not data:
        log.warning("Resposta da API veio vazia.")
        return {}

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")

    log.info("Dados salvos em: %s", output_path)
    return data
