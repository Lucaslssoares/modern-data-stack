import json
from pathlib import Path

import pandas as pd

from common.logger import get_logger

log = get_logger(__name__)


def flatten_to_bronze(raw_path: str, source_name: str = "api") -> pd.DataFrame:
    """
    Lê o JSON bruto e aplana estruturas aninhadas para a camada Bronze.

    Não aplica nenhuma transformação de negócio — apenas normalização
    estrutural. Toda a lógica de domínio fica na camada Silver do dbt.

    Parâmetros
    ----------
    raw_path    : caminho para o arquivo JSON gerado pelo Extract
    source_name : identificador da fonte (gravado em _source para rastreabilidade)

    AJUSTE AQUI se a API retornar uma estrutura diferente:
      - Lista de registros:  pd.json_normalize(data, record_path='items')
      - Objeto único:        pd.json_normalize(data)   ← padrão atual
    """
    path = Path(raw_path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {raw_path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    df = pd.json_normalize(data)

    # Metadados de rastreabilidade (padrão Bronze)
    df["_loaded_at"] = pd.Timestamp.now(tz="UTC")
    df["_source"]    = source_name

    log.info("Bronze pronto — %d linha(s), %d colunas", len(df), len(df.columns))
    return df
