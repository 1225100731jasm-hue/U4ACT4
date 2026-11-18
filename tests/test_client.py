import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from restconf_client import RestconfClient  # noqa: E402


@pytest.fixture(autouse=True)
def credenciales(monkeypatch):
    monkeypatch.setenv("SANDBOX_USER", "developer")
    monkeypatch.setenv("SANDBOX_PASS", "secreto")


def respuesta(status, texto="", datos=None):
    r = MagicMock()
    r.status_code = status
    r.text = texto
    r.json.return_value = datos
    return r


def test_url_se_arma_bien():
    c = RestconfClient("10.10.20.181", 443)
    assert c._url("a/b") == "https://10.10.20.181:443/restconf/data/a/b"


def test_get_404_devuelve_none():
    with patch("restconf_client.requests.get", return_value=respuesta(404)):
        assert RestconfClient("h").get("x") is None


def test_get_200_devuelve_json():
    resp = respuesta(200, "{}", {"a": 1})
    with patch("restconf_client.requests.get", return_value=resp):
        assert RestconfClient("h").get("x") == {"a": 1}


def test_put_devuelve_codigo():
    with patch("restconf_client.requests.put", return_value=respuesta(204)):
        assert RestconfClient("h").put("x", {"a": 1}) == 204


def test_verify_ssl_false_por_defecto():
    assert RestconfClient("h").verify is False


def test_verify_ssl_true_con_variable(monkeypatch):
    monkeypatch.setenv("VERIFY_SSL", "true")
    assert RestconfClient("h").verify is True
