import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from payloads import build_items, is_subset  # noqa: E402

with open(ROOT / "config" / "vars.yml", encoding="utf-8") as f:
    CFG = yaml.safe_load(f)


def test_cuatro_recursos():
    assert len(build_items(CFG)) == 4


def test_loopback_ip_en_payload():
    path, body = build_items(CFG)[0]
    assert "Loopback=201" in path
    prim = body["Cisco-IOS-XE-native:Loopback"]["ip"]["address"]["primary"]
    assert prim["address"] == CFG["loopback"]["ip"]


def test_loopback_mascara_y_descripcion():
    _, body = build_items(CFG)[0]
    lb = body["Cisco-IOS-XE-native:Loopback"]
    assert lb["ip"]["address"]["primary"]["mask"] == CFG["loopback"]["mask"]
    assert lb["description"] == CFG["loopback"]["description"]


def test_snmp_community_en_ruta_y_payload():
    path, body = build_items(CFG)[1]
    assert path.endswith("community=DEVOPS-RO")
    assert body["Cisco-IOS-XE-snmp:community"]["name"] == "DEVOPS-RO"
    assert body["Cisco-IOS-XE-snmp:community"]["RO"] == [None]


def test_snmp_location_y_contact():
    items = dict(build_items(CFG))
    loc = [b for p, b in items.items() if p.endswith("snmp:location")][0]
    con = [b for p, b in items.items() if p.endswith("snmp:contact")][0]
    assert loc["Cisco-IOS-XE-snmp:location"] == "Lab-DevNet"
    assert con["Cisco-IOS-XE-snmp:contact"] == "equipo@ejemplo.com"


def test_todas_las_rutas_usan_native():
    for path, _ in build_items(CFG):
        assert path.startswith("Cisco-IOS-XE-native:native/")


def test_is_subset():
    assert is_subset({"a": 1}, {"a": 1, "b": 2})
    assert not is_subset({"a": 1}, {"a": 2})


def test_is_subset_anidado():
    assert is_subset({"a": {"b": 1}}, {"a": {"b": 1, "c": 2}})
    assert not is_subset({"a": {"b": 1}}, {"a": {"c": 2}})


def test_is_subset_numero_contra_texto():
    assert is_subset({"name": 201}, {"name": "201"})


def test_is_subset_lista_de_un_elemento():
    assert is_subset({"x": {"n": 1}}, {"x": [{"n": 1, "m": 2}]})
    assert not is_subset({"x": {"n": 1}}, {"x": [{"n": 9}]})
