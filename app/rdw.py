import json
from datetime import date

import requests

from app.models import Vehicle

RDW_URL = "https://opendata.rdw.nl/resource/m9d7-ebf2.json"


def normalize_kenteken(kenteken: str) -> str:
    return kenteken.replace(" ", "").replace("-", "").upper()


def fetch_raw(kenteken: str) -> list[dict]:
    response = requests.get(RDW_URL, params={"kenteken": normalize_kenteken(kenteken)}, timeout=10)
    response.raise_for_status()
    return response.json()


def parse_vehicle(data: dict) -> Vehicle:
    return Vehicle(
        kenteken=data["kenteken"],
        merk=data["merk"],
        model=data["handelsbenaming"],
        voertuigsoort=data["voertuigsoort"],
        eerste_toelating=date.fromisoformat(data["datum_eerste_toelating"]),
        catalogusprijs=int(data["catalogusprijs"]) if data.get("catalogusprijs") else None,
    )


def fetch_vehicle(kenteken: str) -> Vehicle | None:
    raw_data = fetch_raw(kenteken)
    if not raw_data:
        return None
    return parse_vehicle(raw_data[0])
