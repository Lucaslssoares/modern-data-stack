import json
from pathlib import Path

import requests

from common.logger import get_logger

log = get_logger(__name__)


def extract_data(
    url: str,
    output_path: str = "data/raw_inmet.json",
    token: str = None,
) -> list | dict:
    """
    GET na URL e salva JSON bruto em output_path.

    Parâmetros
    ----------
    url         : endpoint da API
    output_path : caminho para salvar o JSON bruto
    token       : se informado, enviado no header "token" (padrão INMET)
    """
    log.info("Extraindo dados de: %s", url.split("?")[0])

    headers = {}
    if token:
        headers["token"] = token

    response = requests.get(url, headers=headers, timeout=30)

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

    n = len(data) if isinstance(data, list) else 1
    log.info("Dados salvos em: %s (%d registro(s))", output_path, n)
    return data
