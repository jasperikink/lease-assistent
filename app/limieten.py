import time
from collections import defaultdict, deque

MAX_TEKENS_PER_BERICHT = 1500
MAX_BERICHTEN_IN_GESPREK = 6
MAX_VRAGEN_PER_UUR = 15

_vragen: dict[str, deque] = defaultdict(deque)


def binnen_limiet(sleutel: str, nu: float | None = None) -> bool:
    nu = time.monotonic() if nu is None else nu
    vragen = _vragen[sleutel]
    while vragen and nu - vragen[0] > 3600:
        vragen.popleft()
    if len(vragen) >= MAX_VRAGEN_PER_UUR:
        return False
    vragen.append(nu)
    return True


def kort_in(berichten: list[dict]) -> list[dict]:
    recent = berichten[-MAX_BERICHTEN_IN_GESPREK:]
    while recent and recent[0]["role"] != "user":
        recent = recent[1:]
    return recent
