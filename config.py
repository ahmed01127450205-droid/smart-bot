import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"
    database_path: str = "data/bot.sqlite3"
    max_file_size_mb: int = 15
    history_messages: int = 10

    @classmethod
    def from_env(cls) -> "Settings":
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not token or not api_key:
            raise RuntimeError(
                "Set TELEGRAM_BOT_TOKEN and GEMINI_API_KEY environment variables."
            )
        return cls(
            telegram_bot_token=token,
            gemini_api_key=api_key,
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            database_path=os.getenv("DATABASE_PATH", "data/bot.sqlite3"),
            max_file_size_mb=max(1, int(os.getenv("MAX_FILE_SIZE_MB", "15"))),
            history_messages=max(0, int(os.getenv("HISTORY_MESSAGES", "10"))),
        )
