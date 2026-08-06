from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    allowed_origins: str = "*"

    def allowed_origins_list(self) -> list[str]:
        origins = [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]
        return origins or ["*"]


settings = Settings()
