from datetime import date

from app.models import LeaseRequest, Vehicle
from app.rules import check_acceptance, leeftijd_in_maanden

VANDAAG = date(2026, 10, 19)

AUDI = Vehicle(
    kenteken="H702BH", merk="AUDI", model="AUDI E-TRON",
    voertuigsoort="Personenauto", eerste_toelating=date(2019, 12, 23),
)


def test_hele_maanden():
    assert leeftijd_in_maanden(date(2019, 12, 23), date(2026, 10, 23)) == 82


def test_maand_telt_niet_als_dag_nog_niet_bereikt_is():
    assert leeftijd_in_maanden(date(2019, 12, 23), date(2026, 10, 19)) == 81


def test_nieuwe_auto_is_nul():
    assert leeftijd_in_maanden(date(2026, 10, 19), date(2026, 10, 19)) == 0


def aanvraag(**wijzigingen) -> LeaseRequest:
    standaard = dict(aankoopprijs=40_000, looptijd_maanden=36, kvk_maanden=24)
    return LeaseRequest(**{**standaard, **wijzigingen})


def test_alles_in_orde():
    result = check_acceptance(AUDI, aanvraag(), VANDAAG)
    assert result.geaccepteerd is True
    assert result.redenen == []


def test_te_oud_aan_het_einde():
    result = check_acceptance(AUDI, aanvraag(looptijd_maanden=48), VANDAAG)
    assert result.geaccepteerd is False
    assert len(result.redenen) == 1


def test_te_oud_bij_start_geeft_een_reden():
    oud = AUDI.model_copy(update={"eerste_toelating": date(2015, 3, 1)})
    result = check_acceptance(oud, aanvraag(), VANDAAG)
    assert result.geaccepteerd is False
    assert len(result.redenen) == 1


def test_starter_zonder_genoeg_aanbetaling():
    result = check_acceptance(AUDI, aanvraag(kvk_maanden=3, aanbetaling=2_000), VANDAAG)
    assert result.geaccepteerd is False


def test_starter_met_genoeg_aanbetaling():
    result = check_acceptance(AUDI, aanvraag(kvk_maanden=3, aanbetaling=8_000), VANDAAG)
    assert result.geaccepteerd is True


def test_motor_mag_niet():
    motor = AUDI.model_copy(update={"voertuigsoort": "Motorfiets"})
    result = check_acceptance(motor, aanvraag(), VANDAAG)
    assert result.geaccepteerd is False


def test_aankoopprijs_te_laag():
    result = check_acceptance(AUDI, aanvraag(aankoopprijs=4_000), VANDAAG)
    assert result.geaccepteerd is False
    assert len(result.redenen) == 1


def test_verzamelt_alle_redenen():
    result = check_acceptance(
        AUDI, aanvraag(aankoopprijs=4_000, looptijd_maanden=84, slottermijn_pct=0.5), VANDAAG
    )
    assert len(result.redenen) >= 3
