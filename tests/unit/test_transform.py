import json
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from transform_data import (
    convert_datetime_columns,
    create_dataframe,
    drop_columns,
    rename_columns,
)


@pytest.fixture
def raw_json_file(tmp_path):
    data = {"id": 1, "ts": 1700000000, "valor": 99.9, "status": "ativo"}
    p = tmp_path / "raw_data.json"
    p.write_text(json.dumps(data))
    return str(p)


def test_create_dataframe_returns_df(raw_json_file):
    df = create_dataframe(raw_json_file)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert "id" in df.columns


def test_create_dataframe_raises_if_missing():
    with pytest.raises(FileNotFoundError):
        create_dataframe("/nao/existe/raw.json")


def test_drop_columns_removes_correct_cols():
    df = pd.DataFrame({"a": [1], "b": [2], "c": [3]})
    with patch("transform_data.cfg") as mock_cfg:
        mock_cfg.COLUMNS_TO_DROP = ["b", "c"]
        result = drop_columns(df)
    assert "a" in result.columns
    assert "b" not in result.columns


def test_rename_columns_applies_mapping():
    df = pd.DataFrame({"old_name": [1], "other": [2]})
    with patch("transform_data.cfg") as mock_cfg:
        mock_cfg.COLUMNS_TO_RENAME = {"old_name": "new_name"}
        result = rename_columns(df)
    assert "new_name" in result.columns
    assert "old_name" not in result.columns


def test_convert_datetime_unix_to_aware(raw_json_file):
    df = pd.DataFrame({"ts": [1700000000]})
    with patch("transform_data.cfg") as mock_cfg:
        mock_cfg.DATETIME_COLUMNS = ["ts"]
        mock_cfg.TIMEZONE = "America/Sao_Paulo"
        result = convert_datetime_columns(df)
    assert pd.api.types.is_datetime64_any_dtype(result["ts"])
