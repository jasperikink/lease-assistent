import pytest
from fastapi.testclient import TestClient

from app import agent
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def geen_wachtwoord(monkeypatch):
    monkeypatch.delenv("DEMO_WACHTWOORD", raising=False)


def test_chat(monkeypatch):
    antwoord = {"antwoord": "Kan.", "tools": ["controleer_lease"], "controle": None, "voertuig": None}
    monkeypatch.setattr(agent, "ask", lambda berichten: antwoord)
    res = client.post("/chat", json={"berichten": [{"role": "user", "content": "hoi"}]})
    assert res.status_code == 200
    assert res.json() == antwoord


def test_chat_zonder_berichten():
    assert client.post("/chat", json={"berichten": []}).status_code == 400


def test_fout_in_agent_geeft_leesbare_melding(monkeypatch):
    def kapot(berichten):
        raise RuntimeError("API onbereikbaar")

    monkeypatch.setattr(agent, "ask", kapot)
    res = client.post("/chat", json={"berichten": [{"role": "user", "content": "hoi"}]})
    assert res.status_code == 502
    assert "API onbereikbaar" in res.json()["detail"]


def test_serveert_de_react_app():
    assert "Lease-assistent" in client.get("/").text


def test_zonder_wachtwoord_geen_toegang(monkeypatch):
    monkeypatch.setenv("DEMO_WACHTWOORD", "geheim")
    res = client.post("/chat", json={"berichten": [{"role": "user", "content": "hoi"}]})
    assert res.status_code == 401


def test_met_goed_wachtwoord_toegang(monkeypatch):
    monkeypatch.setenv("DEMO_WACHTWOORD", "geheim")
    assert client.post("/inloggen", headers={"x-wachtwoord": "geheim"}).status_code == 204
    assert client.post("/inloggen", headers={"x-wachtwoord": "fout"}).status_code == 401
