from pathlib import Path

from pydantic import BaseSettings


class Settings(BaseSettings):
    google_service_account_file: str
    tg_token: str
    wb_url: str

    class Config:
        env_prefix = "RASHODIKI_BOT_"
        case_sensitive = False


_settings = None


def init_settings(env_file: str):
    global _settings
    _settings = Settings(_env_file=env_file)


def settings() -> Settings:
    return _settings
