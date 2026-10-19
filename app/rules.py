from datetime import date

from app.models import AcceptanceResult, LeaseRequest, Vehicle

TOEGESTANE_SOORTEN = {"Personenauto", "Bedrijfsauto"}
MAX_LEEFTIJD_START = 8 * 12
MAX_LEEFTIJD_EINDE = 10 * 12
MIN_LOOPTIJD = 12
MAX_LOOPTIJD = 72
MIN_AANKOOPPRIJS = 5_000
MAX_SLOTTERMIJN = 0.30
STARTER_GRENS_MAANDEN = 6
STARTER_MIN_AANBETALING = 0.20


def leeftijd_in_maanden(eerste_toelating: date, vandaag: date) -> int:
    """Bereken de leeftijd van een auto in maanden.

    Als de dag van vandaag nog niet bereikt is in de huidige maand, telt die maand niet mee.
    """
    jaren = vandaag.year - eerste_toelating.year
    maanden = vandaag.month - eerste_toelating.month
    if vandaag.day < eerste_toelating.day:
        maanden -= 1
    return jaren * 12 + maanden


def euro(bedrag: float) -> str:
    return "€" + f"{bedrag:,.0f}".replace(",", ".")


def check_acceptance(vehicle: Vehicle, aanvraag: LeaseRequest, vandaag: date) -> AcceptanceResult:
    redenen = []

    if vehicle.voertuigsoort not in TOEGESTANE_SOORTEN:
        redenen.append(
            f"We financieren geen {vehicle.voertuigsoort.lower()}, "
            "alleen personenauto's en bedrijfsauto's."
        )

    leeftijd_start = leeftijd_in_maanden(vehicle.eerste_toelating, vandaag)
    if leeftijd_start > MAX_LEEFTIJD_START:
        redenen.append(
            f"De auto is nu {leeftijd_start} maanden oud, het maximum bij de start "
            f"is {MAX_LEEFTIJD_START} maanden (8 jaar). Kies een jongere auto."
        )

    leeftijd_einde = leeftijd_start + aanvraag.looptijd_maanden
    if leeftijd_start <= MAX_LEEFTIJD_START and leeftijd_einde > MAX_LEEFTIJD_EINDE:
        max_looptijd = MAX_LEEFTIJD_EINDE - leeftijd_start
        redenen.append(
            f"Aan het einde van het contract is de auto {leeftijd_einde} maanden oud, "
            f"het maximum is {MAX_LEEFTIJD_EINDE} maanden (10 jaar). "
            f"Kies een looptijd van maximaal {max_looptijd} maanden."
        )

    if not MIN_LOOPTIJD <= aanvraag.looptijd_maanden <= MAX_LOOPTIJD:
        redenen.append(
            f"Een looptijd van {aanvraag.looptijd_maanden} maanden kan niet, "
            f"kies tussen {MIN_LOOPTIJD} en {MAX_LOOPTIJD} maanden."
        )

    if aanvraag.aankoopprijs < MIN_AANKOOPPRIJS:
        redenen.append(
            f"Het aankoopbedrag van {euro(aanvraag.aankoopprijs)} is te laag, "
            f"het minimum is {euro(MIN_AANKOOPPRIJS)}."
        )

    if aanvraag.slottermijn_pct > MAX_SLOTTERMIJN:
        redenen.append(
            f"Een slottermijn van {aanvraag.slottermijn_pct:.0%} is te hoog, "
            f"het maximum is {MAX_SLOTTERMIJN:.0%}."
        )

    if aanvraag.kvk_maanden < STARTER_GRENS_MAANDEN:
        nodig = STARTER_MIN_AANBETALING * aanvraag.aankoopprijs
        if aanvraag.aanbetaling < nodig:
            redenen.append(
                f"De ondernemer staat {aanvraag.kvk_maanden} maanden bij de KvK. "
                f"Korter dan {STARTER_GRENS_MAANDEN} maanden betekent minimaal "
                f"{STARTER_MIN_AANBETALING:.0%} aanbetaling: {euro(nodig)} in plaats van "
                f"{euro(aanvraag.aanbetaling)}."
            )

    return AcceptanceResult(geaccepteerd=not redenen, redenen=redenen)
