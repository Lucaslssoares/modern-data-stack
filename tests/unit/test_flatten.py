import json
from pathlib import Path

import pandas as pd
import pytest

from flatten_data import flatten_to_bronze


@pytest.fixture
def raw_json_file(tmp_path):
    data = {"id": 1, "valor": 99.9, "info": {"tipo": "A"}}
    p = tmp_path / "raw_data.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return str(p)


def test_flatten_returns_dataframe(raw_json_file):
    df = flatten_to_bronze(raw_json_file)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1


def test_flatten_adds_metadata_columns(raw_json_file):
    df = flatten_to_bronze(raw_json_file)
    assert "_loaded_at" in df.columns
    assert "_source" in df.columns


def test_flatten_loaded_at_is_utc(raw_json_file):
    df = flatten_to_bronze(raw_json_file)
    assert df["_loaded_at"].dt.tz is not None


def test_flatten_source_name(raw_json_file):
    df = flatten_to_bronze(raw_json_file, source_name="test_api")
    assert df["_source"].iloc[0] == "test_api"


def test_flatten_raises_if_file_missing():
    with pytest.raises(FileNotFoundError):
        flatten_to_bronze("/nao/existe/raw.json")


def test_flatten_nested_json_is_normalized(raw_json_file):
    """json_normalize deve aplanar campos aninhados (info.tipo → info.tipo)."""
    df = flatten_to_bronze(raw_json_file)
    assert "info.tipo" in df.columns
