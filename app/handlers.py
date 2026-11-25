from telegram import Update
from telegram.ext import ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.effective_user is None:
        return

    allowed_user_id = context.application.bot_data["telegram_user_id"]

    if update.effective_user.id != allowed_user_id:
        await update.message.reply_text("Access denied.")
        return

    await update.message.reply_text("Hi! Bot is working.")
