"""Settings from .env / environment. The ids are written by `make env` from the Terraform outputs."""

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    aws_profile: str | None = None
    aws_region: str = "ap-southeast-2"
    knowledge_base_id: str = ""
    agent_id: str = ""
    agent_alias_id: str = ""
    retrieve_top_k: int = 5


settings = Settings()
