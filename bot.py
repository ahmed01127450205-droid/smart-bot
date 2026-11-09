import logging

from telegram.ext import ApplicationBuilder

from config import Settings
from database import initialize_database
from gemini_service import GeminiService
from handlers import register_handlers


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        level=logging.INFO,
    )
    settings = Settings.from_env()
    initialize_database(settings.database_path)

    application = ApplicationBuilder().token(settings.telegram_bot_token).build()
    application.bot_data["settings"] = settings
    application.bot_data["gemini"] = GeminiService(settings.gemini_api_key, settings.gemini_model)
    register_handlers(application)

    logging.getLogger(__name__).info("Telegram bot is starting")
    application.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
