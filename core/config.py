"""Application configuration loaded from environment variables."""

from functools import lru_cache
import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class Settings(BaseModel):
    tinyfish_api_key: str | None = None
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.8-flash"
    database_url: str = "sqlite:///finsight.db"
    request_timeout_seconds: float = Field(default=30.0, gt=0)
    mock_mode: bool = False

    @property
    def use_mock_mode(self) -> bool:
        return self.mock_mode or not self.tinyfish_api_key


@lru_cache
def get_settings() -> Settings:
    return Settings(
        tinyfish_api_key=os.getenv("TINYFISH_API_KEY"),
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///finsight.db"),
        request_timeout_seconds=float(os.getenv("REQUEST_TIMEOUT_SECONDS", "15")),
        mock_mode=os.getenv("MOCK_MODE", "false").lower() in {"1", "true", "yes"},
    )
