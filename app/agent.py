import json
import os
from datetime import date
from typing import Literal

import requests
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool

from app import calc, rag, rdw, rules
from app.models import LeaseRequest, Vehicle

load_dotenv()

RDW_NIET_BEREIKBAAR = {"fout": "De RDW is tijdelijk niet bereikbaar. Probeer het zo opnieuw."}


def niet_gevonden(kenteken: str) -> dict:
    return {"fout": f"Kenteken {kenteken} niet gevonden bij de RDW."}


@tool
def zoek_voertuig(kenteken: str) -> dict:
    """Zoek merk, model, voertuigsoort en datum eerste toelating op bij de RDW."""
    try:
        vehicle = rdw.fetch_vehicle(kenteken)
    except requests.RequestException:
        return RDW_NIET_BEREIKBAAR
    if vehicle is None:
        return niet_gevonden(kenteken)
    return vehicle.model_dump(mode="json")


@tool
def controleer_lease(
    aankoopprijs: float,
    looptijd_maanden: int,
    kenteken: str | None = None,
    omschrijving: str | None = None,
    voertuigsoort: Literal["Personenauto", "Bedrijfsauto"] = "Personenauto",
    kvk_maanden: int | None = None,
    kvk_sinds: str | None = None,
    aanbetaling: float = 0,
    slottermijn_pct: float = 0,
) -> dict:
    """Controleer een lease tegen het acceptatiebeleid en bereken rente en maandbedrag.

    Gebruikte auto: geef het kenteken. Nieuwe auto die nog geen kenteken heeft: laat kenteken leeg,
    geef merk en model als omschrijving en kies de voertuigsoort (een bestelbus is een Bedrijfsauto).
    KvK-duur als kvk_maanden of als inschrijfdatum kvk_sinds (YYYY-MM-DD). Onbekend: laat beide leeg.
    slottermijn_pct is een fractie, 0.1 is 10%. Aanbetaling en slottermijn niet genoemd: 0.
    """
    vandaag = date.today()
    if kenteken:
        try:
            vehicle = rdw.fetch_vehicle(kenteken)
        except requests.RequestException:
            return RDW_NIET_BEREIKBAAR
        if vehicle is None:
            return niet_gevonden(kenteken)
    else:
        vehicle = Vehicle(
            kenteken="",
            merk="",
            model=omschrijving or "Nieuwe auto",
            voertuigsoort=voertuigsoort,
            eerste_toelating=vandaag,
        )

    kvk_onbekend = kvk_maanden is None and kvk_sinds is None
    if kvk_sinds:
        kvk_maanden = rules.leeftijd_in_maanden(date.fromisoformat(kvk_sinds), vandaag)

    aanvraag = LeaseRequest(
        aankoopprijs=aankoopprijs,
        aanbetaling=aanbetaling,
        slottermijn_pct=slottermijn_pct,
        looptijd_maanden=looptijd_maanden,
        kvk_maanden=rules.STARTER_GRENS_MAANDEN if kvk_onbekend else kvk_maanden,
    )
    oordeel = rules.check_acceptance(vehicle, aanvraag, vandaag)
    rente = calc.bepaal_rente(rules.leeftijd_in_maanden(vehicle.eerste_toelating, vandaag))
    bedrag = None
    if oordeel.geaccepteerd:
        bedrag = calc.maandbedrag(aankoopprijs, aanbetaling, slottermijn_pct, looptijd_maanden, rente)

    resultaat = {
        "voertuig": vehicle.model_dump(mode="json"),
        "invoer": {
            "aankoopprijs": aankoopprijs,
            "aanbetaling": aanbetaling,
            "slottermijn_pct": slottermijn_pct,
            "looptijd_maanden": looptijd_maanden,
            "kvk_maanden": None if kvk_onbekend else kvk_maanden,
            "kvk_sinds": kvk_sinds,
        },
        "geaccepteerd": oordeel.geaccepteerd,
        "redenen": oordeel.redenen,
        "rente_pct": rente,
        "maandbedrag": bedrag,
        "slottermijn_eind": round(slottermijn_pct * aankoopprijs, 2),
        "nieuw": not kenteken,
    }
    if kvk_onbekend:
        resultaat["let_op"] = (
            "KvK-duur onbekend. Bij minder dan 6 maanden is minimaal 20% aanbetaling nodig: "
            f"{rules.euro(0.2 * aankoopprijs)}."
        )
    return resultaat


@tool
def zoek_in_beleid(vraag: str) -> list[dict]:
    """Zoek in het handboek: acceptatiebeleid, algemene voorwaarden, producten, aanvraagproces, FAQ en werkinstructies.
    Gebruik dit voor elke vraag over regels, voorwaarden, btw, aflossen, documenten of het proces.
    Het handboek is Nederlands: stel de zoekvraag altijd in het Nederlands, ook als de klant Engels schrijft."""
    return [
        {"document": p.metadata["titel"], "sectie": p.metadata["sectie"], "tekst": p.page_content}
        for p in rag.zoek(vraag, k=3)
    ]


TOOLS = [zoek_voertuig, controleer_lease, zoek_in_beleid]

SYSTEM_PROMPT = """Je bent de assistent van een leaseadviseur bij een financial lease-maatschappij.
De adviseur plakt berichten van klanten (vaak van WhatsApp) en wil snel weten of een lease kan.
Vandaag is het {vandaag}.

Werkwijze:
- Haal kenteken, aankoopprijs en looptijd uit het bericht. Ontbreekt de prijs of de looptijd, vraag er dan kort naar.
- Nieuwe auto die nog geen kenteken heeft: controleer zonder kenteken, met merk en model als omschrijving.
  Vraag dan niet om een kenteken. Geen kenteken en niet duidelijk of de auto nieuw is: vraag dat kort.
- Aanbetaling of slottermijn niet genoemd: gebruik 0, vraag er niet naar.
- KvK-duur: geef een datum door als kvk_sinds. "Sinds juli" zonder jaar is de meest recente juli
  die al voorbij is. Weet je het helemaal niet, laat het leeg en controleer toch.
- Controleer altijd meteen met controleer_lease als je prijs, looptijd en een kenteken of nieuwe auto hebt.
- Vragen over regels en voorwaarden: gebruik zoek_in_beleid. Antwoord alleen op basis van de gevonden
  passages en noem document en sectie, bijvoorbeeld (Algemene voorwaarden, artikel 7).
  Staat het antwoord er niet in, zeg dat dan en verwijs naar de afdeling Acceptatie.

Regels:
- Reken nooit zelf en beslis nooit zelf of iets mag. Dat doen de tools.
- Bij een afwijzing: noem de redenen en het alternatief dat in de redenen staat.

Vorm van je antwoord:
- Eerste regel: de conclusie in één zin, met het maandbedrag als het kan.
- Daarna maximaal vier korte punten met de belangrijkste details of aannames.
- Sluit af met "Bericht aan de klant:" en een kort, vriendelijk WhatsApp-bericht in je/jij-vorm.
- Geen kopjes. Hooguit 120 woorden, het klantbericht niet meegerekend.
- Schrijft de klant Engels, schrijf het klantbericht dan in het Engels. De rest van je antwoord is voor de
  adviseur en blijft Nederlands, net als "Bericht aan de klant:".
"""


def maak_agent():
    workspace = os.getenv("ANTHROPIC_WORKSPACE_ID")
    llm = ChatAnthropic(
        model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5"),
        max_tokens=1024,
        default_headers={"anthropic-workspace-id": workspace} if workspace else None,
    )
    prompt = SYSTEM_PROMPT.format(vandaag=date.today().isoformat())
    return create_agent(model=llm, tools=TOOLS, system_prompt=prompt)


def lees_tool_resultaat(message) -> dict | list | None:
    try:
        data = json.loads(message.content)
    except (TypeError, ValueError):
        return None
    if isinstance(data, dict) and "fout" in data:
        return None
    return data


def ask(berichten: list[dict]) -> dict:
    result = maak_agent().invoke({"messages": berichten}, config={"recursion_limit": 10})
    tools = []
    controle = None
    voertuig = None
    bronnen = []

    for message in result["messages"]:
        tools += [call["name"] for call in getattr(message, "tool_calls", None) or []]
        if message.type != "tool":
            continue
        data = lees_tool_resultaat(message)
        if data is None:
            continue
        if message.name == "controleer_lease":
            controle = data
            voertuig = data["voertuig"]
        elif message.name == "zoek_voertuig":
            voertuig = data
        elif message.name == "zoek_in_beleid":
            bronnen += [b for b in data if b not in bronnen]

    return {
        "antwoord": result["messages"][-1].text,
        "tools": tools,
        "controle": controle,
        "voertuig": voertuig,
        "bronnen": bronnen,
    }


if __name__ == "__main__":
    import sys

    print(ask([{"role": "user", "content": " ".join(sys.argv[1:])}]))
