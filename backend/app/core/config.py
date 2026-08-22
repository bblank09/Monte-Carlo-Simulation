from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ALLOWED_ORIGINS = (
    "http://localhost:5173,http://127.0.0.1:5173,"
    "http://localhost:8000,http://127.0.0.1:8000"
)


def resolve_project_path(path: Path) -> Path:
    """Resolve configured relative paths from the repository, not the cwd."""
    return path if path.is_absolute() else PROJECT_ROOT / path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Keep the original MC variable working while accepting the sibling
    # project's SEC_API_KEY convention in local shells and GitHub Actions.
    sec_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("SEC_API_KEY", "SEC_OPENDATA_API_KEY"),
    )
    sec_api_base_url: str = Field(
        default="https://api.sec.or.th",
        validation_alias=AliasChoices("SEC_API_BASE_URL"),
    )
    data_dir: Path = Path("data")
    processed_dir: Path = Path("data/processed")
    runs_dir: Path = Path("data/runs")
    max_persisted_runs: int = Field(default=500, ge=1, le=10_000)
    allowed_origins: str = DEFAULT_ALLOWED_ORIGINS

    def allowed_origins_list(self) -> list[str]:
        origins = [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]
        return origins or DEFAULT_ALLOWED_ORIGINS.split(",")


settings = Settings()
