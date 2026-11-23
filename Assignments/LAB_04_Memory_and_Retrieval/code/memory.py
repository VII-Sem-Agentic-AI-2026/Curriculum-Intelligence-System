"""
Lab 4 — Memory & Retrieval.

RunState is short-term (dies with the run). RevisionHistoryRetriever is the
long-term store, and — LangChain integration point #2 — it's a real
`langchain_core.retrievers.BaseRetriever` subclass, so it plugs into any
LangChain chain/graph the standard way (`.invoke(query)`), not a bespoke
lookup function. It reads its corpus through the MCP connector
(`read_revision_history`), and ranks with local TF-IDF + cosine similarity
(see the docstring below for why, not a hosted embedding API).

Pitfall to avoid (per the book): "don't conflate run state with the archive
-- mixing them corrupts the baseline." RunState and the retriever are kept
fully separate classes, never merged.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from . import mcp_client


@dataclass
class RunState:
    """Short-term state. One instance per run. Never persisted long-term."""
    run_id: str
    draft: Any = None
    current_step: str | None = None
    clarified_request: dict | None = None
    plan: Any = None


class RevisionHistoryRetriever(BaseRetriever):
    """
    Long-term store: prior curriculum-revision decisions, reached via MCP
    (`read_revision_history`). Similarity search uses local TF-IDF, not a
    hosted embedding API — this sandbox has no network path to an embedding
    provider, and TF-IDF is a legitimate, fully local substitute that keeps
    the retrieval acceptance test real instead of faked. Swapping in a
    hosted embedding model later only touches `_build_index`.
    """
    k: int = 5
    model_config = {"arbitrary_types_allowed": True}

    def _items(self) -> list[dict]:
        return mcp_client.mcp_read_revision_history()["items"]

    def retrieve_by_tags(self, tags: list[str]) -> list[dict]:
        tagset = {t.lower() for t in tags}
        return [item for item in self._items() if tagset & {t.lower() for t in item.get("tags", [])}]

    def _get_relevant_documents(self, query: str, *, run_manager=None) -> list[Document]:
        items = self._items()
        if not items:
            return []
        corpus = [item["text"] for item in items]
        vectorizer = TfidfVectorizer(stop_words="english")
        matrix = vectorizer.fit_transform(corpus)
        query_vec = vectorizer.transform([query])
        sims = cosine_similarity(query_vec, matrix).flatten()
        ranked_idx = sims.argsort()[::-1][: self.k]
        docs = []
        for idx in ranked_idx:
            if sims[idx] <= 0:
                continue
            item = items[idx]
            docs.append(Document(page_content=item["text"],
                                  metadata={**{k: v for k, v in item.items() if k != "text"},
                                            "similarity_score": round(float(sims[idx]), 4)}))
        return docs
