# Lab 4 — Memory & Retrieval

**Concept (book spec):** Separate short-term run state from long-term stored knowledge; retrieve by tags and by similarity.

## 1. Concept applied
RunState and the long-term retriever are genuinely separate classes with no shared reference. The retriever reaches its corpus only through the MCP connector and supports both tag filtering and similarity ranking, proven to rank the most relevant real committee resolution first.

## 2. Technical stack

| Item | Used |
|---|---|
| Short-term | RunState dataclass |
| Long-term | RevisionHistoryRetriever, a real langchain_core.retrievers.BaseRetriever |
| Similarity | TF-IDF + cosine similarity, local, no external API |

## 3. Code

- `code/memory.py` (full copy of `app/memory.py` in the main codebase)

**app/memory.py** (excerpt):
```python
term store: prior curriculum-revision decisions, reached via MCP
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

```

## 4. Evidence

See `evidence.txt` in this folder — output of:

```
python -m pytest tests/test_langchain_memory_skills.py::test_retriever_is_langchain_and_ranks_relevant_first tests/test_langchain_memory_skills.py::test_run_state_is_not_persistent -v
```

```
platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0 -- /usr/bin/python3
cachedir: .pytest_cache
rootdir: /home/claude/cis3
plugins: platformdirs-4.13.0, anyio-4.16.0, langsmith-0.14.17
collecting ... collected 2 items

tests/test_langchain_memory_skills.py::test_retriever_is_langchain_and_ranks_relevant_first PASSED [ 50%]
tests/test_langchain_memory_skills.py::test_run_state_is_not_persistent PASSED [100%]

```
