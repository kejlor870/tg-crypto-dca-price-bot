import os
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler

from app.config import load_config
from app.handlers import start
from database.database import Database
from database.transaction_repository import TransactionRepository
from services.transaction_service import TransactionService


# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# load_dotenv(os.path.join(BASE_DIR, ".env"))
#
# BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
# _raw_user_id = os.getenv("ALLOWED_USER_ID", "0").strip()
# try:
#     ALLOWED_USER_ID = int(_raw_user_id)
# except ValueError:
#     ALLOWED_USER_ID = 0
#
# DATA_FILE = os.path.join(BASE_DIR, "zakupy.txt")
# TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def main() -> None:
    config = load_config()

    # config.database_path.parent.mkdir(
    #     parents=True,
    #     exist_ok=True,
    # )
    #
    # db = Database(str(config.database_path))
    #
    # try:
    #     db.initialize()
    #
    #     repository = TransactionRepository(db.connection)
    #     service = TransactionService(repository)
    #
    #     service.rebuild_portfolios()
    #
    #     print("Application initialized successfully.")
    #     print(f"Loaded portfolios: {len(service.get_all_portfolios())}")
    #
    # finally:
    #     db.close()

    application = (
        Application.builder().token(config.telegram_bot_token).build()
    )

    application.bot_data["telegram_user_id"] = config.telegram_user_id
    application.add_handler(CommandHandler("start", start))

    print("Bot is starting...")
    application.run_polling()


if __name__ == "__main__":
    print("Started!")
    main()
