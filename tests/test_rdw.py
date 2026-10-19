from datetime import date

from app import rdw
from app.rdw import normalize_kenteken, parse_vehicle


def test_delete_hyphens():
    assert normalize_kenteken("H-702-BH") == "H702BH"


def test_delete_spaces():
    assert normalize_kenteken("H 702 BH") == "H702BH"


def test_makes_uppercase():
    assert normalize_kenteken("h702bh") == "H702BH"


AUDI_RAW = {
    "kenteken": "H702BH",
    "voertuigsoort": "Personenauto",
    "merk": "AUDI",
    "handelsbenaming": "AUDI E-TRON",
    "datum_eerste_toelating": "20191223",
    "catalogusprijs": "114053",
}


def test_parse_vehicle_zet_datum_om():
    vehicle = parse_vehicle(AUDI_RAW)
    assert vehicle.eerste_toelating == date(2019, 12, 23)


def test_parse_vehicle_zet_catalogusprijs_om():
    vehicle = parse_vehicle(AUDI_RAW)
    assert vehicle.catalogusprijs == 114053


def test_parse_vehicle_zet_catalogusprijs_op_none_als_niet_aanwezig():
    raw = AUDI_RAW.copy()
    del raw["catalogusprijs"]
    vehicle = parse_vehicle(raw)
    assert vehicle.catalogusprijs is None


def test_fetch_vehicle_geeft_none_als_kenteken_niet_bestaat(monkeypatch):
    monkeypatch.setattr(rdw, "fetch_raw", lambda kenteken: [])
    assert rdw.fetch_vehicle("H-702-BH") is None


def test_fetch_vehicle_geeft_vehicle_als_kenteken_bestaat(monkeypatch):
    monkeypatch.setattr(rdw, "fetch_raw", lambda kenteken: [AUDI_RAW])
    vehicle = rdw.fetch_vehicle("H-702-BH")
    assert vehicle.merk == "AUDI"
