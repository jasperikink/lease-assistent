def bepaal_rente(leeftijd_maanden: int) -> float:
    if leeftijd_maanden < 36:
        return 6.9
    elif leeftijd_maanden < 72:
        return 7.9
    else:
        return 8.9


def maandbedrag(
    aankoopprijs: float,
    aanbetaling: float,
    slottermijn_pct: float,
    looptijd_maanden: int,
    rente_pct: float,
) -> float:
    slottermijn = slottermijn_pct * aankoopprijs
    af_te_lossen = aankoopprijs - aanbetaling - slottermijn

    if rente_pct == 0:
        return round(af_te_lossen / looptijd_maanden, 2)

    maand_rente = rente_pct / 100 / 12

    aflossing = af_te_lossen * (maand_rente / (1 - (1 + maand_rente) ** -looptijd_maanden))

    rente_slottermijn = slottermijn * maand_rente

    return round(aflossing + rente_slottermijn, 2)
