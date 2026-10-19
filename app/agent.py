import json
import os
from datetime import date

import requests
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool

from app import calc, rag, rdw, rules
from app.models import LeaseRequest

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
    kenteken: str,
    aankoopprijs: float,
    looptijd_maanden: int,
    kvk_maanden: int | None = None,
    kvk_sinds: str | None = None,
    aanbetaling: float = 0,
    slottermijn_pct: float = 0,
) -> dict:
    """Controleer een lease tegen het acceptatiebeleid en bereken rente en maandbedrag.

    KvK-duur als kvk_maanden of als inschrijfdatum kvk_sinds (YYYY-MM-DD). Onbekend: laat beide leeg.
    slottermijn_pct is een fractie, 0.1 is 10%. Aanbetaling en slottermijn niet genoemd: 0.
    """
    try:
        vehicle = rdw.fetch_vehicle(kenteken)
    except requests.RequestException:
        return RDW_NIET_BEREIKBAAR
    if vehicle is None:
        return niet_gevonden(kenteken)

    vandaag = date.today()
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
    }
    if kvk_onbekend:
        resultaat["let_op"] = (
            "KvK-duur onbekend. Bij minder dan 6 maanden is minimaal 20% aanbetaling nodig: "
            f"{rules.euro(0.2 * aankoopprijs)}."
        )
    return resultaat


@tool
def zoek_in_beleid(vraag: str) -> str:
    """Zoek in het acceptatiebeleid en de FAQ. Gebruik dit voor vragen over regels, voorwaarden, btw of het proces."""
    passages = rag.zoek(vraag)
    return "\n\n".join(f"[{p.metadata['sectie']}] ({p.metadata['bron']})\n{p.page_content}" for p in passages)


TOOLS = [zoek_voertuig, controleer_lease, zoek_in_beleid]

SYSTEM_PROMPT = """Je bent de assistent van een leaseadviseur bij een financial lease-maatschappij.
De adviseur plakt berichten van klanten (vaak van WhatsApp) en wil snel weten of een lease kan.
Vandaag is het {vandaag}.

Werkwijze:
- Haal kenteken, aankoopprijs en looptijd uit het bericht. Ontbreekt een van die drie, vraag er dan kort naar.
- Aanbetaling of slottermijn niet genoemd: gebruik 0, vraag er niet naar.
- KvK-duur: geef een datum door als kvk_sinds. "Sinds juli" zonder jaar is de meest recente juli
  die al voorbij is. Weet je het helemaal niet, laat het leeg en controleer toch.
- Controleer altijd meteen met controleer_lease als je kenteken, prijs en looptijd hebt.
- Vragen over regels en voorwaarden: gebruik zoek_in_beleid en noem de sectie.

Regels:
- Reken nooit zelf en beslis nooit zelf of iets mag. Dat doen de tools.
- Bij een afwijzing: noem de redenen en het alternatief dat in de redenen staat.

Vorm van je antwoord:
- Eerste regel: de conclusie in één zin, met het maandbedrag als het kan.
- Daarna maximaal vier korte punten met de belangrijkste details of aannames.
- Sluit af met "Bericht aan de klant:" en een kort, vriendelijk WhatsApp-bericht in je/jij-vorm.
- Geen kopjes. Hooguit 120 woorden, het klantbericht niet meegerekend.
"""


def maak_agent():
    workspace = os.getenv("ANTHROPIC_WORKSPACE_ID")
    llm = ChatAnthropic(
        model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5"),
        default_headers={"anthropic-workspace-id": workspace} if workspace else None,
    )
    prompt = SYSTEM_PROMPT.format(vandaag=date.today().isoformat())
    return create_agent(model=llm, tools=TOOLS, system_prompt=prompt)


def lees_tool_resultaat(message) -> dict | None:
    try:
        data = json.loads(message.content)
    except (TypeError, ValueError):
        return None
    return None if "fout" in data else data


def ask(berichten: list[dict]) -> dict:
    result = maak_agent().invoke({"messages": berichten})
    tools = []
    controle = None
    voertuig = None

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

    return {
        "antwoord": result["messages"][-1].text,
        "tools": tools,
        "controle": controle,
        "voertuig": voertuig,
    }


if __name__ == "__main__":
    import sys

    print(ask([{"role": "user", "content": " ".join(sys.argv[1:])}]))
