from datetime import date

import requests

from app import agent, rdw
from app.models import Vehicle

KIA = Vehicle(kenteken="AB123C", merk="KIA", model="NIRO", voertuigsoort="Personenauto",
              eerste_toelating=date(2024, 1, 15))


def test_controleer_lease_geaccepteerd(monkeypatch):
    monkeypatch.setattr(rdw, "fetch_vehicle", lambda kenteken: KIA)
    result = agent.controleer_lease.invoke({
        "kenteken": "AB-123-C", "aankoopprijs": 25_000, "looptijd_maanden": 48,
        "kvk_maanden": 24, "slottermijn_pct": 0.2,
    })
    assert result["geaccepteerd"] is True
    assert result["maandbedrag"] > 0


def test_controleer_lease_afgewezen(monkeypatch):
    monkeypatch.setattr(rdw, "fetch_vehicle", lambda kenteken: KIA)
    result = agent.controleer_lease.invoke({
        "kenteken": "AB-123-C", "aankoopprijs": 25_000, "looptijd_maanden": 48,
        "kvk_maanden": 24, "slottermijn_pct": 0.5,
    })
    assert result["geaccepteerd"] is False
    assert result["maandbedrag"] is None


def test_rdw_plat_geeft_nette_fout(monkeypatch):
    def plat(kenteken):
        raise requests.ConnectionError("RDW down")

    monkeypatch.setattr(rdw, "fetch_vehicle", plat)
    result = agent.zoek_voertuig.invoke({"kenteken": "AB-123-C"})
    assert "niet bereikbaar" in result["fout"]


def test_zoek_in_beleid_geeft_document_en_sectie():
    bronnen = agent.zoek_in_beleid.invoke({"vraag": "starter zonder jaarcijfers"})
    assert {"document": "Acceptatiebeleid financial lease", "sectie": "Starters"}.items() <= next(
        b for b in bronnen if b["sectie"] == "Starters"
    ).items()


def test_controleer_lease_met_kvk_datum(monkeypatch):
    monkeypatch.setattr(rdw, "fetch_vehicle", lambda kenteken: KIA)
    result = agent.controleer_lease.invoke({
        "kenteken": "AB-123-C", "aankoopprijs": 25_000, "looptijd_maanden": 48,
        "kvk_sinds": date.today().replace(day=1).isoformat(),
    })
    assert result["geaccepteerd"] is False
    assert result["invoer"]["kvk_maanden"] == 0


def test_controleer_lease_zonder_kvk_meldt_dat(monkeypatch):
    monkeypatch.setattr(rdw, "fetch_vehicle", lambda kenteken: KIA)
    result = agent.controleer_lease.invoke({
        "kenteken": "AB-123-C", "aankoopprijs": 25_000, "looptijd_maanden": 48,
    })
    assert result["geaccepteerd"] is True
    assert "KvK-duur onbekend" in result["let_op"]


def test_nieuwe_auto_zonder_kenteken(monkeypatch):
    def niet_aanroepen(kenteken):
        raise AssertionError("geen RDW zonder kenteken")

    monkeypatch.setattr(rdw, "fetch_vehicle", niet_aanroepen)
    result = agent.controleer_lease.invoke({
        "omschrijving": "Volkswagen ID. Buzz Cargo", "voertuigsoort": "Bedrijfsauto",
        "aankoopprijs": 52_000, "looptijd_maanden": 60, "kvk_maanden": 60, "slottermijn_pct": 0.15,
    })
    assert result["geaccepteerd"] is True
    assert result["nieuw"] is True
    assert result["rente_pct"] == 6.9
    assert result["voertuig"]["model"] == "Volkswagen ID. Buzz Cargo"
    assert result["voertuig"]["voertuigsoort"] == "Bedrijfsauto"


def test_nieuwe_auto_volgt_verder_het_beleid():
    result = agent.controleer_lease.invoke({
        "omschrijving": "Kia EV3", "aankoopprijs": 38_000, "looptijd_maanden": 84, "kvk_maanden": 24,
    })
    assert result["geaccepteerd"] is False
    assert any("84 maanden" in r for r in result["redenen"])
