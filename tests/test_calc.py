import pytest

from app.calc import bepaal_rente, maandbedrag


@pytest.mark.parametrize("leeftijd_maanden, rente", [
    (0, 6.9),
    (35, 6.9),
    (36, 7.9),
    (71, 7.9),
    (72, 8.9),
])
def test_bepaal_rente(leeftijd_maanden, rente):
    assert bepaal_rente(leeftijd_maanden) == rente


def test_zonder_rente():
    assert maandbedrag(18_500, 0, 0, 60, 0) == 308.33


def test_gewone_lening():
    assert maandbedrag(10_000, 0, 0, 12, 6.0) == 860.66


def test_met_aanbetaling_en_slottermijn():
    assert maandbedrag(30_000, 3_000, 0.2, 60, 7.9) == 464.30


def test_slottermijn_verlaagt_maandbedrag():
    zonder = maandbedrag(30_000, 0, 0, 60, 7.9)
    met = maandbedrag(30_000, 0, 0.3, 60, 7.9)
    assert met < zonder
