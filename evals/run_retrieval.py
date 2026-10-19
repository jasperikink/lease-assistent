import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from app import rag

load_dotenv()

VRAGEN = json.loads((Path(__file__).parent / "retrieval.json").read_text())


def positie(retriever: rag.Retriever, vraag: str, verwacht: str) -> int | None:
    ids = [doc.metadata["id"] for doc in retriever.zoek(vraag, k=retriever.aantal)]
    return ids.index(verwacht) + 1 if verwacht in ids else None


def evalueer(retriever: rag.Retriever) -> dict:
    posities = [positie(retriever, v["vraag"], v["verwacht"]) for v in VRAGEN]
    n = len(posities)
    return {
        "posities": posities,
        "hit@1": sum(p == 1 for p in posities) / n,
        "hit@3": sum(p is not None and p <= 3 for p in posities) / n,
        "mrr": sum(1 / p for p in posities if p) / n,
    }


def main():
    chunks = rag.load_chunks()
    retrievers = {"bm25": rag.Retriever(chunks)}
    embeddings = rag.maak_embeddings()
    if embeddings:
        retrievers["hybrid"] = rag.Retriever(chunks, embeddings)
    else:
        print("Geen VOYAGE_API_KEY: alleen BM25.\n", file=sys.stderr)

    resultaten = {naam: evalueer(r) for naam, r in retrievers.items()}

    namen = list(resultaten)
    print(f"{'vraag':<52}" + "".join(f"{n:>8}" for n in namen))
    for i, v in enumerate(VRAGEN):
        rij = "".join(f"{resultaten[n]['posities'][i] or '-':>8}" for n in namen)
        print(f"{v['vraag'][:50]:<52}{rij}")
    print()
    for metric in ("hit@1", "hit@3", "mrr"):
        print(f"{metric:<52}" + "".join(f"{resultaten[n][metric]:>8.2f}" for n in namen))


if __name__ == "__main__":
    main()
