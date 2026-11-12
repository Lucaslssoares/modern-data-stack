import json
from pathlib import Path

import pandas as pd
import pytest

from flatten_data import flatten_to_bronze


@pytest.fixture
def raw_json_file(tmp_path):
    # Formato colunar da Open-Meteo
    data = {
        "latitude": -1.88,
        "longitude": -48.77,
        "elevation": 12.0,
        "timezone": "America/Belem",
        "hourly": {
            "time": ["2026-01-01T00:00", "2026-01-01T01:00"],
            "temperature_2m": [25.1, 24.8],
            "precipitation": [0.0, 1.2],
        },
    }
    p = tmp_path / "raw_data.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return str(p)


def test_flatten_returns_dataframe(raw_json_file):
    df = flatten_to_bronze(raw_json_file)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2


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


def test_flatten_hourly_vira_linhas_com_metadados(raw_json_file):
    """Cada hora vira uma linha e os metadados do ponto se repetem em todas."""
    df = flatten_to_bronze(raw_json_file)
    assert list(df["temperature_2m"]) == [25.1, 24.8]
    assert (df["latitude"] == -1.88).all()
    assert (df["timezone"] == "America/Belem").all()
