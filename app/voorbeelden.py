import random
from concurrent.futures import ThreadPoolExecutor

import requests

from app import rdw
from app.models import Vehicle

JONGE_AUTO = "voertuigsoort='Personenauto' AND datum_eerste_toelating_dt > '2023-01-01T00:00:00'"
BESTELBUS = "voertuigsoort='Bedrijfsauto' AND datum_eerste_toelating_dt > '2021-01-01T00:00:00'"


def willekeurig(where: str) -> Vehicle | None:
    params = {"$where": where, "$limit": 1, "$offset": random.randint(0, 500)}
    try:
        res = requests.get(rdw.RDW_URL, params=params, timeout=5)
        res.raise_for_status()
        data = res.json()
        return rdw.parse_vehicle(data[0]) if data else None
    except Exception:
        return None


def vraagprijs(vehicle: Vehicle | None, factor: float, standaard: int) -> int:
    if vehicle is None or not vehicle.catalogusprijs:
        return standaard
    return int(round(vehicle.catalogusprijs * factor, -2))


def bedrag(waarde: int) -> str:
    return f"{waarde:,}".replace(",", ".")


def naam(vehicle: Vehicle) -> str:
    model = vehicle.model if vehicle.model.startswith(vehicle.merk) else f"{vehicle.merk} {vehicle.model}"
    return model.title()


def maak_voorbeelden() -> list[dict]:
    with ThreadPoolExecutor(max_workers=2) as pool:
        auto, bus = pool.map(willekeurig, [JONGE_AUTO, BESTELBUS])

    berichten = [
        {
            "afzender": "Lotte, fotograaf",
            "tijd": "09:12",
            "tekst": "Hoi! Ik sta sinds juli bij de KvK. Ik wil de Audi met kenteken H-702-BH kopen "
            "voor 42.000, 48 maanden, 10% slottermijn. Kan dat?",
        },
    ]

    if auto:
        berichten.append({
            "afzender": "Daan, IT-consultant",
            "tijd": "10:47",
            "tekst": f"Goedemorgen, ik heb een {naam(auto)} gevonden, kenteken {auto.kenteken}, "
            f"vraagprijs {bedrag(vraagprijs(auto, 0.75, 32000))} euro. Ik wil 48 maanden en 5.000 aanbetalen. "
            "Mijn bedrijf bestaat sinds 2021. Wat wordt het per maand?",
        })
    else:
        berichten.append({
            "afzender": "Daan, IT-consultant",
            "tijd": "10:47",
            "tekst": "Goedemorgen, ik heb een Renault Clio gevonden, kenteken XX-999-X, vraagprijs 14.950 euro. "
            "Ik wil 48 maanden en 2.000 aanbetalen. Mijn bedrijf bestaat sinds 2021. Wat wordt het per maand?",
        })

    if bus:
        berichten.append({
            "afzender": "Mehmet, klusbedrijf",
            "tijd": "11:30",
            "tekst": f"Hallo, voor mijn klusbedrijf zoek ik een bus: de {naam(bus)} met kenteken {bus.kenteken}. "
            f"Prijs {bedrag(vraagprijs(bus, 0.6, 24000))}, liefst 60 maanden met 20% slottermijn. "
            "Ingeschreven sinds 2018.",
        })

    berichten.append({
        "afzender": "Sanne, schilder",
        "tijd": "13:05",
        "tekst": "Moet ik bij financial lease de btw in één keer betalen?",
    })
    return berichten
