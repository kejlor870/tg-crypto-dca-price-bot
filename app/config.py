import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Config:
    telegram_bot_token: str
    telegram_user_id: int
    database_path: Path


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN")
    user_id = os.getenv("ALLOWED_USER_ID")
    database_path = os.getenv("DATABASE_PATH")

    if not token or not token.strip():
        raise ValueError("Missing BOT_TOKEN in .env")

    if not user_id or not user_id.strip():
        raise ValueError("Missing ALLOWED_USER_ID in .env")

    if not database_path or not database_path.strip():
        raise ValueError("Missing DATABASE_PATH in .env")

    try:
        parsed_user_id = int(user_id)
    except ValueError as exc:
        raise ValueError("ALLOWED_USER_ID must be an integer.") from exc

    if parsed_user_id <= 0:
        raise ValueError("ALLOWED_USER_ID must be greater than zero.")

    parsed_database_path = Path(database_path.strip())

    if not parsed_database_path.is_absolute():
        parsed_database_path = PROJECT_ROOT / parsed_database_path

    return Config(
        telegram_bot_token=token.strip(),
        telegram_user_id=parsed_user_id,
        database_path=parsed_database_path,
    )
