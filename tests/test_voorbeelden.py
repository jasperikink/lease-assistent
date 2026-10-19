from datetime import date

import requests

from app import voorbeelden


class Antwoord:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


KIA = {
    "kenteken": "AB123C", "merk": "KIA", "handelsbenaming": "NIRO", "voertuigsoort": "Personenauto",
    "datum_eerste_toelating": "20240115", "catalogusprijs": "40000",
}


def test_voorbeelden_met_rdw(monkeypatch):
    monkeypatch.setattr(voorbeelden.requests, "get", lambda *a, **kw: Antwoord([KIA]))
    berichten = voorbeelden.maak_voorbeelden()
    assert len(berichten) == 4
    assert "AB123C" in berichten[1]["tekst"]
    assert "30.000" in berichten[1]["tekst"]


def test_voorbeelden_zonder_rdw(monkeypatch):
    def plat(*a, **kw):
        raise requests.ConnectionError("RDW down")

    monkeypatch.setattr(voorbeelden.requests, "get", plat)
    berichten = voorbeelden.maak_voorbeelden()
    assert len(berichten) == 3
    assert "XX-999-X" in berichten[1]["tekst"]
