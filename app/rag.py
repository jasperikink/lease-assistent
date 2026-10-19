import os
import re
from pathlib import Path

import requests
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import MarkdownHeaderTextSplitter

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
VOYAGE_URL = "https://api.voyageai.com/v1/embeddings"

STOPWOORDEN = {
    "de", "het", "een", "en", "van", "ik", "je", "is", "in", "op", "te", "mag", "kan",
    "wat", "hoe", "met", "zit", "als", "er", "dat", "die", "voor", "aan", "bij", "of",
    "mijn", "we", "wij", "zijn", "wordt", "worden", "moet", "niet", "nog", "ook",
}


def stam(woord: str) -> str:
    if len(woord) > 4 and woord.endswith("s"):
        return woord[:-1]
    return woord


def tokenize(tekst: str) -> list[str]:
    woorden = re.findall(r"[a-z0-9à-ÿ]+", tekst.lower())
    return [stam(w) for w in woorden if w not in STOPWOORDEN]


def load_chunks(data_dir: Path = DATA_DIR) -> list[Document]:
    splitter = MarkdownHeaderTextSplitter([("#", "titel"), ("##", "sectie")])
    chunks = []
    for pad in sorted(data_dir.glob("*.md")):
        tekst = "\n".join(r for r in pad.read_text().splitlines() if not r.startswith(">"))
        for doc in splitter.split_text(tekst):
            if "sectie" not in doc.metadata:
                continue
            doc.page_content = f"{doc.metadata['sectie']}\n{doc.page_content}"
            doc.metadata["bron"] = pad.name
            doc.metadata["id"] = f"{pad.name}#{doc.metadata['sectie']}"
            chunks.append(doc)
    return chunks


class VoyageEmbeddings(Embeddings):
    def __init__(self, api_key: str, model: str = "voyage-3.5"):
        self.api_key = api_key
        self.model = model

    def _embed(self, teksten: list[str], input_type: str) -> list[list[float]]:
        res = requests.post(
            VOYAGE_URL,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"input": teksten, "model": self.model, "input_type": input_type},
            timeout=30,
        )
        res.raise_for_status()
        return [d["embedding"] for d in sorted(res.json()["data"], key=lambda d: d["index"])]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed(texts, "document")

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text], "query")[0]


def reciprocal_rank_fusion(rankings: list[list[Document]], k: int = 60) -> list[Document]:
    scores: dict[str, float] = {}
    docs: dict[str, Document] = {}
    for ranking in rankings:
        for positie, doc in enumerate(ranking):
            doc_id = doc.metadata["id"]
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + positie + 1)
            docs[doc_id] = doc
    return [docs[doc_id] for doc_id in sorted(scores, key=scores.get, reverse=True)]


class Retriever:
    def __init__(self, chunks: list[Document], embeddings: Embeddings | None = None):
        self.aantal = len(chunks)
        self.bm25 = BM25Retriever.from_documents(chunks, preprocess_func=tokenize, k=self.aantal)
        self.vectoren = InMemoryVectorStore.from_documents(chunks, embeddings) if embeddings else None

    @property
    def modus(self) -> str:
        return "hybrid" if self.vectoren else "bm25"

    def zoek(self, vraag: str, k: int = 3) -> list[Document]:
        rankings = [self.bm25.invoke(vraag)]
        if self.vectoren:
            rankings.append(self.vectoren.similarity_search(vraag, k=self.aantal))
        return reciprocal_rank_fusion(rankings)[:k]


def maak_embeddings() -> Embeddings | None:
    api_key = os.getenv("VOYAGE_API_KEY")
    if not api_key:
        return None
    return VoyageEmbeddings(api_key, os.getenv("VOYAGE_MODEL", "voyage-3.5"))


_retriever = None


def get_retriever() -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = Retriever(load_chunks(), maak_embeddings())
    return _retriever


def zoek(vraag: str, k: int = 3) -> list[Document]:
    return get_retriever().zoek(vraag, k)
