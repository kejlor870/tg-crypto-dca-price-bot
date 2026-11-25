from telegram import Update
from telegram.ext import ContextTypes

from app.keyboards import main_menu_keyboard


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.effective_user is None:
        return

    allowed_user_id = context.application.bot_data["telegram_user_id"]

    if update.effective_user.id != allowed_user_id:
        await update.message.reply_text("Access denied.")
        return

    await update.message.reply_text("Hi! Bot is working.", reply_markup=main_menu_keyboard())


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    if query is None or update.effective_user is None:
        return

    allowed_user_id = context.application.bot_data["telegram_user_id"]

    if update.effective_user.id != allowed_user_id:
        await query.answer("Access denied.", show_alert=True)
        return

    await query.answer()

    if query.data == "portfolio":
        service = context.application.bot_data["transaction_service"]

        portfolios = service.get_all_portfolios()

        # Get active portfolios
        active_portfolios = [
            portfolio
            for portfolio in portfolios
            if portfolio.quantity > 0
        ]

        if not active_portfolios:
            message = "📊 Your portfolio is empty."
        else:
            lines = ["📊 Your portfolio", ""]

            for portfolio in active_portfolios:
                lines.append(f"🪙 {portfolio.symbol}")
                lines.append(f"Quantity: {portfolio.quantity}")
                lines.append(
                    f"Average buy price: "
                    f"{portfolio.average_buy_price} USDC"
                )
                lines.append(f"Total cost: {portfolio.total_cost} USDC")
                lines.append("")

            message = "\n".join(lines).rstrip()

    elif query.data == "history":
        service = context.application.bot_data["transaction_service"]
        transactions = service.get_all_transactions()

        if not transactions:
            message = "📜 Transaction history is empty."
        else:
            lines = ["📜 Transaction history", ""]

            for transaction in transactions[:10]:
                lines.append(f"{'🟢' if transaction.transaction_type.value == 'BUY' else '🔴'} {transaction.transaction_type.value}")
                lines.append(f"{transaction.symbol}")
                lines.append(f"Quantity: {transaction.quantity}")
                lines.append(f"Price: {transaction.price}")
                lines.append(f"Date: {transaction.created_at.strftime('%Y-%m-%d %H:%M')}")
                lines.append("")

            message = "\n".join(lines).rstrip()

            if transactions > 10:
                message += "\n\nShowing the 10 most recent transactions."

    else:
        messages = {
            "buy": "Add bought crypto.",
            "sell": "Add sold crypto.",
        }

        message = messages.get(query.data, "Unknown option.")

    if query.message:
        await query.message.reply_text(message, reply_markup=main_menu_keyboard())
