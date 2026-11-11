"""Settings from .env / environment (`make env` fills the AWS ids from the Terraform outputs).
Empty VECTOR_BUCKET → local numpy index; empty TOOLS_LAMBDA → tools run in-process. Both = fully local mode."""

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    google_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"
    embedding_model: str = "gemini-embedding-001"
    embedding_dimension: int = 768
    aws_profile: str | None = None
    aws_region: str = "ap-southeast-2"
    docs_bucket: str = ""
    vector_bucket: str = ""
    vector_index: str = "handbook"
    tools_lambda: str = ""
    api_url: str = ""
    api_token: str = ""
    local_index_path: str = ".ka/index.npz"
    retrieve_top_k: int = 4
    max_steps: int = 6


settings = Settings()
