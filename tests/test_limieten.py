from app import limieten


def test_limiet_per_uur(monkeypatch):
    monkeypatch.setattr(limieten, "_vragen", limieten.defaultdict(limieten.deque))
    for i in range(limieten.MAX_VRAGEN_PER_UUR):
        assert limieten.binnen_limiet("1.2.3.4", nu=i)
    assert not limieten.binnen_limiet("1.2.3.4", nu=100)
    assert limieten.binnen_limiet("5.6.7.8", nu=100)
    assert limieten.binnen_limiet("1.2.3.4", nu=4000)


def test_kort_gesprek_in_en_begint_bij_gebruiker():
    berichten = [{"role": "user" if i % 2 == 0 else "assistant", "content": str(i)} for i in range(9)]
    kort = limieten.kort_in(berichten)
    assert len(kort) <= limieten.MAX_BERICHTEN_IN_GESPREK
    assert kort[0]["role"] == "user"
    assert kort[-1]["content"] == "8"
