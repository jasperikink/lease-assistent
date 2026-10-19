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


def test_eerste_keer_lotte_en_sanne(monkeypatch):
    monkeypatch.setattr(voorbeelden.requests, "get", lambda *a, **kw: Antwoord([KIA]))
    berichten = voorbeelden.maak_voorbeelden()
    teksten = [b["tekst"] for b in berichten]
    assert len(berichten) == 4
    assert "H-702-BH" in teksten[0]
    assert "AB123C" in teksten[1]
    assert "30.000" in teksten[1]
    assert voorbeelden.SANNE["tekst"] in teksten


def test_zonder_rdw_toch_vier_berichten(monkeypatch):
    def plat(*a, **kw):
        raise requests.ConnectionError("RDW down")

    monkeypatch.setattr(voorbeelden.requests, "get", plat)
    berichten = voorbeelden.maak_voorbeelden()
    assert len(berichten) == 4
    assert "H-702-BH" in berichten[0]["tekst"]


def test_nieuwe_berichten_wisselen(monkeypatch):
    monkeypatch.setattr(voorbeelden.requests, "get", lambda *a, **kw: Antwoord([]))
    sets = {tuple(b["tekst"] for b in voorbeelden.maak_voorbeelden(nieuw=True)) for _ in range(20)}
    assert len(sets) > 1


def test_tijden_lopen_op(monkeypatch):
    monkeypatch.setattr(voorbeelden.requests, "get", lambda *a, **kw: Antwoord([KIA]))
    tijden = [b["tijd"] for b in voorbeelden.maak_voorbeelden(nieuw=True)]
    assert tijden == sorted(tijden)
    assert len(set(tijden)) == len(tijden)
