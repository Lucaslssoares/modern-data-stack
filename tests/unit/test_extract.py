import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from extract_data import extract_data


@pytest.fixture
def sample_api_response():
    return {"id": 1, "value": 42.5, "status": "ok"}


def test_extract_saves_json(tmp_path, sample_api_response):
    """Deve salvar a resposta da API como JSON válido."""
    output = str(tmp_path / "raw_data.json")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = sample_api_response

    with patch("extract_data.requests.get", return_value=mock_resp):
        result = extract_data("https://api.exemplo.com/test", output_path=output)

    assert result == sample_api_response
    saved = json.loads(Path(output).read_text())
    assert saved["id"] == 1


def test_extract_raises_on_http_error():
    """Deve lançar RuntimeError quando a API retornar status != 200."""
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.text = "Unauthorized"

    with patch("extract_data.requests.get", return_value=mock_resp):
        with pytest.raises(RuntimeError, match="HTTP 401"):
            extract_data("https://api.exemplo.com/test")


def test_extract_returns_empty_on_empty_response():
    """Deve retornar dict vazio quando a API retornar corpo vazio."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {}

    with patch("extract_data.requests.get", return_value=mock_resp):
        result = extract_data("https://api.exemplo.com/test")

    assert result == {}
