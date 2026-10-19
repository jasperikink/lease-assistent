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


def test_zoek_in_beleid_noemt_sectie():
    assert "[Starters]" in agent.zoek_in_beleid.invoke({"vraag": "starter zonder jaarcijfers"})


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
