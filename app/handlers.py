from decimal import InvalidOperation, Decimal

from telegram import Update
from telegram.ext import ContextTypes

from app.keyboards import main_menu_keyboard


# --------------------- START ---------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.effective_user is None:
        return

    allowed_user_id = context.application.bot_data["telegram_user_id"]

    if update.effective_user.id != allowed_user_id:
        await update.message.reply_text("Access denied.")
        return

    await update.message.reply_text("Hi! Bot is working.", reply_markup=main_menu_keyboard())


# --------------------- MENU BUTTONS HANDLERS ---------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    if query is None or update.effective_user is None:
        return

    allowed_user_id = context.application.bot_data["telegram_user_id"]

    if update.effective_user.id != allowed_user_id:
        await query.answer("Access denied.", show_alert=True)
        return

    await query.answer()

    # ---- PORTFOLIO BUTTON ----
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

    # ---- HISTORY BUTTON ----
    elif query.data == "history":
        service = context.application.bot_data["transaction_service"]
        transactions = service.get_all_transactions()

        if not transactions:
            message = "📜 Transaction history is empty."
        else:
            lines = ["📜 Transaction history", ""]

            for transaction in transactions[:10]:
                lines.append(
                    f"{'🟢' if transaction.transaction_type.value == 'BUY' else '🔴'}"
                    f" {transaction.transaction_type.value} | {transaction.symbol}"
                )
                lines.append(f"Quantity: {transaction.quantity}")
                lines.append(f"Price: {transaction.price}")
                lines.append(f"Date: {transaction.created_at.strftime('%Y-%m-%d %H:%M')}")
                lines.append("")

            message = "\n".join(lines).rstrip()

            if len(transactions) > 10:
                message += "\n\nShowing the 10 most recent transactions."

    else:
        messages = {
            "buy": "Use: /buy SYMBOL QUANTITY PRICE",
            "sell": "Use: /sell SYMBOL QUANTITY PRICE",
        }

        message = messages.get(query.data, "Unknown option.")

    if query.message:
        await query.message.reply_text(message, reply_markup=main_menu_keyboard())


# --------------------- MENU BUTTONS HANDLERS ---------------------
async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _handle_transaction_command(update, context, "BUY")


async def sell_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _handle_transaction_command(update, context, "SELL")


async def _handle_transaction_command(update: Update, context: ContextTypes.DEFAULT_TYPE, operation: str) -> None:
    if update.effective_user is None or update.message is None:
        return

    allowed_user_id = context.application.bot_data["telegram_user_id"]

    if update.effective_user.id != allowed_user_id:
        await update.message.reply_text("Access denied.")
        return

    if len(context.args) != 3:
        await update.message.reply_text(
            f"Usage: /{operation.lower()} SYMBOL QUANTITY PRICE\n"
            f"Example: /{operation.lower()} BTC 0.025 90000"
        )
        return

    symbol, quantity_text, price_text = context.args

    try:
        quantity = Decimal(quantity_text)
        price = Decimal(price_text)

    except InvalidOperation:
        await update.message.reply_text("Quantity and price must be valid numbers.")
        return

    if (
            not quantity.is_finite()
            or not price.is_finite()
            or quantity <= 0
            or price <= 0
    ):
        await update.message.reply_text("Quantity and price must be finite numbers greater than zero.")
        return

    service = context.application.bot_data["transaction_service"]

    try:
        if operation == "BUY":
            transaction = service.add_buy(symbol, quantity, price)
        elif operation == "SELL":
            transaction = service.add_sell(symbol, quantity, price)

    except (ValueError, TypeError) as exc:
        await update.message.reply_text(f"Transaction not saved: {exc}")
        return

    await update.message.reply_text(
        f"{'🟢' if transaction.transaction_type.value == 'BUY' else '🔴'}"
        " Transaction saved successfully!\n"
        f"Type: {transaction.transaction_type.value}\n"
        f"Symbol: {transaction.symbol}\n"
        f"Quantity: {transaction.quantity}\n"
        f"Price: {transaction.price} USDC\n"
        f"Total: {transaction.value} USDC"
    )
