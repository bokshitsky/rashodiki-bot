import json
import os
from pathlib import Path

from pydantic import BaseSettings


class Settings(BaseSettings):
    google_service_account_file: str
    tg_token: str
    db_url: str

    class Config:
        env_prefix = "RASHODIKI_BOT_"
        case_sensitive = False


_settings = Settings(_env_file=os.environ.get("RASHODIKI_ENV_FILE", "config.env"))


def settings() -> Settings:
    return _settings


bot_google_email = json.loads(Path(settings().google_service_account_file).read_text())["client_email"]
