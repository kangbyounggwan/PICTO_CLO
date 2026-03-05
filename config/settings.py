import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


def get_int_env(key: str, default: int = 0) -> int:
    """환경변수를 int로 변환 (빈 문자열 처리)"""
    value = os.getenv(key, "")
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


class Settings(BaseModel):
    # API Keys
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")

    # Telegram Bots (3개)
    marky_bot_token: str = os.getenv("MARKY_BOT_TOKEN", "")
    servo_bot_token: str = os.getenv("SERVO_BOT_TOKEN", "")
    scout_bot_token: str = os.getenv("SCOUT_BOT_TOKEN", "")

    # Telegram
    telegram_group_id: int | None = get_int_env("TELEGRAM_GROUP_ID") or None

    # Team Members (authorized users)
    ceo_user_id: int = get_int_env("CEO_USER_ID")
    cto_user_id: int = get_int_env("CTO_USER_ID")

    # Database
    database_path: Path = Path(os.getenv("DATABASE_PATH", "./database/bot.db"))

    # Gemini
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
    max_tokens: int = 4096

    @property
    def authorized_users(self) -> list[int]:
        """권한이 있는 사용자 ID 목록"""
        return [uid for uid in [self.ceo_user_id, self.cto_user_id] if uid]

settings = Settings()
