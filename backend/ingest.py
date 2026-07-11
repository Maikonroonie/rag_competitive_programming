import json
from pathlib import Path

from app.config import settings
from app.rag import RagStore

DATA_DIR = Path(__file__).parent / "data"


# load json into qdrant
def main() -> None:
    store = RagStore()
    print("Tworzenie kolekcji (dense + sparse BM25)...")
    store.recreate_collections()

    concepts = json.loads((DATA_DIR / "concepts" / "concepts.json").read_text(encoding="utf8"))
    concept_docs = [
        {"title": c["title"], "kind": "concept", "text": c["text"]}
        for c in concepts
    ]

    problems = json.loads((DATA_DIR / "solutions" / "problems.json").read_text(encoding="utf8"))
    editorial_docs = []
    code_docs = []
    for p in problems:
        tags = ", ".join(p["tags"])
        editorial_docs.append(
            {
                "title": f"{p['title']} ({p['source']})",
                "kind": "editorial",
                "text": f"Zadanie: {p['title']}. Tagi: {tags}. Trudność: {p['difficulty']}.\n{p['editorial']}",
            }
        )
        search_text = (
            f"Wzorcowa implementacja: {p['title']}. Tagi: {tags}. "
            f"Język: {p['code_language']}.\n{p['editorial']}"
        )
        code_docs.append(
            {
                "title": f"{p['title']} — implementacja ({p['code_language']})",
                "kind": "code",
                "text": f"{search_text}\n\nKod wzorcowy:\n```{p['code_language']}\n{p['code']}\n```",
            }
        )

    print(f"Ingest: {len(concept_docs)} konceptów + {len(editorial_docs)} editoriali -> {settings.concepts_collection}")
    store.add_documents(settings.concepts_collection, concept_docs + editorial_docs)

    print(f"Ingest: {len(code_docs)} implementacji -> {settings.solutions_collection}")
    store.add_documents(settings.solutions_collection, code_docs)

    print("Gotowe.")


if __name__ == "__main__":
    main()
