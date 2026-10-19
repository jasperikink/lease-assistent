import pytest
from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding

from app import rag


def test_tokenize_haalt_stopwoorden_en_leestekens_weg():
    assert rag.tokenize("Kan ik als Starters leasen?") == ["starter", "leasen"]


def test_load_chunks_heeft_sectie_en_bron():
    chunks = rag.load_chunks()
    assert len(chunks) >= 40
    for chunk in chunks:
        assert chunk.metadata["sectie"]
        assert chunk.metadata["bron"].endswith(".md")
        assert "Fictief" not in chunk.page_content


@pytest.mark.parametrize("vraag, sectie", [
    ("Ik sta pas 3 maanden ingeschreven, kan ik als starter leasen?", "Starters"),
    ("Hoe oud mag de auto zijn?", "Leeftijd van de auto"),
    ("Kan ik een bestelbus leasen?", "Kan ik een bestelbus leasen?"),
    ("Hoe werkt de btw bij financial lease?", "Wat gebeurt er met de btw?"),
    ("Wat is de maximale slottermijn?", "Slottermijn"),
])
def test_vindt_juiste_sectie(vraag, sectie):
    assert sectie in [doc.metadata["sectie"] for doc in rag.zoek(vraag)]


def test_rrf_zet_document_dat_beide_vinden_bovenaan():
    a, b, c = (Document(page_content=x, metadata={"id": x}) for x in "abc")
    resultaat = rag.reciprocal_rank_fusion([[a, b], [b, c]])
    assert resultaat[0].metadata["id"] == "b"


def test_hybrid_met_nep_embeddings():
    retriever = rag.Retriever(rag.load_chunks(), DeterministicFakeEmbedding(size=32))
    assert retriever.modus == "hybrid"
    assert len(retriever.zoek("Kan ik een bestelbus leasen?")) == 3
