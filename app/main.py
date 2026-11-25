import os
from dotenv import load_dotenv
from telegram.ext import Application, CallbackQueryHandler, CommandHandler

from app.config import load_config
from app.handlers import button_handler, start, buy_command, sell_command
from database.database import Database
from database.transaction_repository import TransactionRepository
from services.transaction_service import TransactionService


def main() -> None:
    config = load_config()

    # Create folder for database if it not exists
    config.database_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    db = Database(str(config.database_path))

    try:
        # Create db table if not exists
        db.initialize()

        # Connect db to repository and service
        repository = TransactionRepository(db.connection)
        service = TransactionService(repository)

        # Rebuild portfolios from saved transactions in db
        service.rebuild_portfolios()

        # Create telegram app
        application = (
            Application.builder().token(config.telegram_bot_token).build()
        )

        # Data for handlers
        application.bot_data["telegram_user_id"] = config.telegram_user_id
        application.bot_data["transaction_service"] = service

        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("buy", buy_command))
        application.add_handler(CommandHandler("sell", sell_command))
        application.add_handler(CallbackQueryHandler(button_handler))

        print("Bot is starting...")
        print("Application initialized successfully.")
        print(f"Loaded portfolios: {len(service.get_all_portfolios())}")
        application.run_polling()

    finally:
        # Close db after bot stop
        db.close()


if __name__ == "__main__":
    print("Started!")
    main()
