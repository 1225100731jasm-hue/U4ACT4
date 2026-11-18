import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import deploy  # noqa: E402
import verify  # noqa: E402
from payloads import build_items  # noqa: E402
import yaml  # noqa: E402

CONFIG = str(ROOT / "config" / "vars.yml")
with open(CONFIG, encoding="utf-8") as f:
    CFG = yaml.safe_load(f)


class FakeClient:
    """Cliente falso: simula el switch sin red."""

    def __init__(self, *args, **kwargs):
        self.estado = {}
        self.puts = []

    def get(self, path):
        return self.estado.get(path)

    def put(self, path, payload):
        self.puts.append(path)
        self.estado[path] = payload
        return 201


def correr(monkeypatch, argv, cliente):
    monkeypatch.setattr(sys, "argv", ["deploy.py"] + argv)
    with patch.object(deploy, "RestconfClient", return_value=cliente):
        return deploy.main()


def test_check_no_modifica_el_equipo(monkeypatch, capsys):
    cli = FakeClient()
    assert correr(monkeypatch, ["--config", CONFIG, "--check"], cli) == 0
    assert cli.puts == []
    assert "4 cambio(s) pendiente(s)" in capsys.readouterr().out


def test_deploy_aplica_los_cuatro_recursos(monkeypatch, capsys):
    cli = FakeClient()
    correr(monkeypatch, ["--config", CONFIG], cli)
    assert len(cli.puts) == 4
    assert "4 cambio(s) aplicado(s)" in capsys.readouterr().out


def test_segunda_ejecucion_es_idempotente(monkeypatch, capsys):
    cli = FakeClient()
    correr(monkeypatch, ["--config", CONFIG], cli)
    cli.puts.clear()
    capsys.readouterr()
    correr(monkeypatch, ["--config", CONFIG], cli)
    salida = capsys.readouterr().out
    assert cli.puts == []
    assert salida.count("[OK]") == 4
    assert "0 cambio(s) aplicado(s)" in salida


def test_corrige_desviacion(monkeypatch):
    cli = FakeClient()
    correr(monkeypatch, ["--config", CONFIG], cli)
    ruta, _ = build_items(CFG)[2]
    cli.estado[ruta] = {"Cisco-IOS-XE-snmp:location": "OTRA-COSA"}
    cli.puts.clear()
    correr(monkeypatch, ["--config", CONFIG], cli)
    assert cli.puts == [ruta]


def test_verify_pass_cuando_coincide(monkeypatch):
    cli = FakeClient()
    for ruta, cuerpo in build_items(CFG):
        cli.estado[ruta] = cuerpo
    monkeypatch.chdir(ROOT)
    with patch.object(verify, "RestconfClient", return_value=cli):
        assert verify.main() == 0


def test_verify_fail_cuando_no_existe(monkeypatch):
    monkeypatch.chdir(ROOT)
    with patch.object(verify, "RestconfClient", return_value=FakeClient()):
        assert verify.main() == 1
