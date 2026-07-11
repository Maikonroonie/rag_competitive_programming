from __future__ import annotations

from qdrant_client import QdrantClient

from .config import settings
from .models import RetrievedDoc


class RagStore:
    # init qdrant
    def __init__(self) -> None:
        if settings.qdrant_url:
            self.client = QdrantClient(url=settings.qdrant_url)
        else:
            self.client = QdrantClient(path=settings.qdrant_path)
        self.client.set_model(settings.dense_model)
        self.client.set_sparse_model(settings.sparse_model)

    # reset collections
    def recreate_collections(self) -> None:
        for name in (settings.concepts_collection, settings.solutions_collection):
            if self.client.collection_exists(name):
                self.client.delete_collection(name)
            self.client.create_collection(
                collection_name=name,
                vectors_config=self.client.get_fastembed_vector_params(),
                sparse_vectors_config=self.client.get_fastembed_sparse_vector_params(),
            )

    # insert documents
    def add_documents(self, collection: str, docs: list[dict]) -> None:
        self.client.add(
            collection_name=collection,
            documents=[d["text"] for d in docs],
            metadata=docs,
        )

    # hybrid search
    def search(
        self,
        query_text: str,
        code_unlocked: bool,
        limit_concepts: int = 4,
        limit_code: int = 2,
    ) -> list[RetrievedDoc]:
        results = self._query(settings.concepts_collection, query_text, limit_concepts)
        if code_unlocked:
            results += self._query(settings.solutions_collection, query_text, limit_code)
        return results

    # query one collection
    def _query(self, collection: str, text: str, limit: int) -> list[RetrievedDoc]:
        if not self.client.collection_exists(collection):
            return []
        hits = self.client.query(
            collection_name=collection,
            query_text=text,
            limit=limit,
        )
        docs = []
        for h in hits:
            meta = h.metadata or {}
            docs.append(
                RetrievedDoc(
                    title=meta.get("title", "?"),
                    kind=meta.get("kind", "concept"),
                    score=h.score or 0.0,
                    snippet=(meta.get("text") or h.document or "")[:1500],
                )
            )
        return docs


_store: RagStore | None = None


# rag singleton
def get_store() -> RagStore:
    global _store
    if _store is None:
        _store = RagStore()
    return _store
