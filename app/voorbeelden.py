import random
from concurrent.futures import ThreadPoolExecutor

import requests

from app import rdw
from app.models import Vehicle

JONGE_AUTO = "voertuigsoort='Personenauto' AND datum_eerste_toelating_dt > '2023-01-01T00:00:00'"
BESTELBUS = "voertuigsoort='Bedrijfsauto' AND datum_eerste_toelating_dt > '2021-01-01T00:00:00'"

LOTTE = {
    "afzender": "Lotte, fotograaf",
    "tekst": "Hoi! Ik sta sinds juli bij de KvK. Ik wil de Audi met kenteken H-702-BH kopen "
    "voor 42.000, 48 maanden, 10% slottermijn. Kan dat?",
}

SANNE = {
    "afzender": "Sanne, schilder",
    "tekst": "Moet ik bij financial lease de btw in één keer betalen?",
}

AANVRAGEN = [
    LOTTE,
    {
        "afzender": "Thomas, architect",
        "tekst": "Goedemiddag, kan ik de Audi H-702-BH leasen? Prijs 39.500, 36 maanden, "
        "4.000 aanbetaling. Mijn bureau bestaat sinds 2019.",
    },
    {
        "afzender": "Mila, interieurstudio",
        "tekst": "Hoi! Ik wil een nieuwe Volkswagen ID. Buzz Cargo bestellen bij de dealer, hij heeft nog geen kenteken. "
        "Prijs 52.000, 60 maanden, 15% slottermijn. Mijn bedrijf bestaat sinds 2020.",
    },
    {
        "afzender": "Fatima, kapsalon",
        "tekst": "Hoi, ik wil de Renault Clio XX-999-X voor 14.950. Kan dat over 60 maanden met 35% slottermijn? "
        "Ik sta 2 jaar bij de KvK.",
    },
    {
        "afzender": "Ruben, hovenier",
        "tekst": "Is de Clio met kenteken XX-999-X te leasen? Vraagprijs 13.500, 24 maanden. "
        "Ik ben 4 maanden geleden begonnen.",
    },
]

BELEIDSVRAGEN = [
    SANNE,
    {"afzender": "Kees, installateur", "tekst": "Kan ik de lease eerder aflossen als het goed gaat? Wat kost dat?"},
    {"afzender": "Noor, fysiotherapeut", "tekst": "Welke documenten moet ik aanleveren voor de aanvraag?"},
    {"afzender": "Bram, loodgieter", "tekst": "Ik heb een paar jaar geleden een BKR-registratie gehad. Kan ik nog leasen?"},
    {"afzender": "Eva, stylist", "tekst": "Ik heb een auto in Duitsland gezien. Kan ik die via jullie leasen?"},
    {"afzender": "Youssef, koerier", "tekst": "Mag ik mijn leaseauto verkopen voordat het contract is afgelopen?"},
]

NAMEN_AUTO = ["Daan, IT-consultant", "Sophie, marketingbureau", "Lars, makelaar", "Iris, tandarts"]
NAMEN_BUS = ["Mehmet, klusbedrijf", "Jeroen, elektricien", "Anouk, cateraar", "Sem, schildersbedrijf"]


def willekeurig(where: str) -> Vehicle | None:
    params = {"$where": where, "$limit": 1, "$offset": random.randint(0, 500)}
    try:
        res = requests.get(rdw.RDW_URL, params=params, timeout=5)
        res.raise_for_status()
        data = res.json()
        return rdw.parse_vehicle(data[0]) if data else None
    except Exception:
        return None


def vraagprijs(vehicle: Vehicle, factor: float, standaard: int) -> int:
    if not vehicle.catalogusprijs:
        return standaard
    return int(round(vehicle.catalogusprijs * factor, -2))


def bedrag(waarde: int) -> str:
    return f"{waarde:,}".replace(",", ".")


def naam(vehicle: Vehicle) -> str:
    model = vehicle.model if vehicle.model.startswith(vehicle.merk) else f"{vehicle.merk} {vehicle.model}"
    return model.title()


def bericht_auto(auto: Vehicle, afzender: str) -> dict:
    return {
        "afzender": afzender,
        "tekst": f"Goedemorgen, ik heb een {naam(auto)} gevonden, kenteken {auto.kenteken}, "
        f"vraagprijs {bedrag(vraagprijs(auto, 0.75, 32000))} euro. Ik wil 48 maanden en 5.000 aanbetalen. "
        "Mijn bedrijf bestaat sinds 2021. Wat wordt het per maand?",
    }


def bericht_bus(bus: Vehicle, afzender: str) -> dict:
    return {
        "afzender": afzender,
        "tekst": f"Hallo, voor mijn bedrijf zoek ik een bus: de {naam(bus)} met kenteken {bus.kenteken}. "
        f"Prijs {bedrag(vraagprijs(bus, 0.6, 24000))}, liefst 60 maanden met 20% slottermijn. "
        "Ingeschreven sinds 2018.",
    }


def met_tijden(berichten: list[dict]) -> list[dict]:
    minuten = sorted(random.sample(range(8 * 60 + 30, 17 * 60), len(berichten)))
    return [{**b, "tijd": f"{m // 60:02d}:{m % 60:02d}"} for b, m in zip(berichten, minuten)]


def maak_voorbeelden(nieuw: bool = False) -> list[dict]:
    with ThreadPoolExecutor(max_workers=2) as pool:
        auto, bus = pool.map(willekeurig, [JONGE_AUTO, BESTELBUS])

    if nieuw:
        berichten = [random.choice(AANVRAGEN)]
        vragen = random.sample(BELEIDSVRAGEN, 3)
    else:
        berichten = [LOTTE]
        vragen = [SANNE, *random.sample(BELEIDSVRAGEN[1:], 2)]

    if auto:
        berichten.append(bericht_auto(auto, random.choice(NAMEN_AUTO)))
    if bus:
        berichten.append(bericht_bus(bus, random.choice(NAMEN_BUS)))
    berichten += vragen[: max(1, 4 - len(berichten))]
    return met_tijden(berichten)
