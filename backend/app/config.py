from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    openai_api_key: str = ""
    openai_base_url: str = ""
    llm_model: str = "gpt-4o-mini"

    qdrant_url: str = ""
    qdrant_path: str = str(BASE_DIR / "qdrant_storage")

    dense_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    sparse_model: str = "Qdrant/bm25"

    concepts_collection: str = "conceptual_data"
    solutions_collection: str = "code_solutions"


settings = Settings()
