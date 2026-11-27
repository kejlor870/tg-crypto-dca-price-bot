from __future__ import annotations

import logging
import sqlite3
from decimal import InvalidOperation, Decimal
from html import escape
from uuid import UUID

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from app.keyboards import main_menu_keyboard, fill_command_keyboard, history_menu_keyboard, history_back_keyboard, \
    history_symbols_keyboard, history_transactions_keyboard, delete_confirmation_keyboard, history_last_keyboard

logger = logging.getLogger(__name__)


# --------------------- START ---------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None:
        return

    allowed_user_id = context.application.bot_data["telegram_user_id"]

    if update.effective_user.id != allowed_user_id:
        if update.message:
            await update.message.reply_text("Access denied.")
        elif update.callback_query:
            await update.callback_query.answer("Access denied.", show_alert=True)
        return

    lines = [
        "💼 <b>Crypto Portfolio Manager</b>",
        "<i>Track your trades, average prices, and holdings in one place.</i>",
        "",
        "<b>Quick Actions:</b>",
        "➕ /buy BTC 0.05 92000 - Log a purchase",
        "➖ /sell BTC 0.02 98000 - Log a sale",
        "📊 /portfolio - View holdings & avg. buy prices",
        "📜 /history - Check transaction history",
        "",
        "👇 <i>Tap a button below or type a command to start:</i>"
    ]

    text = "\n".join(lines).rstrip()
    markup = main_menu_keyboard()

    if update.message:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)

    elif update.callback_query and update.callback_query.message:
        await update.callback_query.message.reply_text(text, parse_mode="HTML", reply_markup=markup)


# Returns portfolio message text
def get_portfolio_messages(context: ContextTypes.DEFAULT_TYPE) -> str:
    services = context.application.bot_data["transaction_service"]
    portfolios = services.get_all_portfolios()

    active_portfolios = [
        portfolio
        for portfolio in portfolios
        if portfolio.quantity > 0
    ]

    if not active_portfolios:
        return "📊 Your portfolio is empty."

    lines = ["📊 <b>Your portfolio:</b>", "──────────────────", ""]

    total_invested = Decimal("0")

    for portfolio in active_portfolios:
        symbol_esc = escape(portfolio.symbol)
        total_invested += portfolio.total_cost

        lines.append(f"<b>{symbol_esc}</b>")
        lines.append(f"├ Holdings: <code>{portfolio.quantity} {symbol_esc}</code>")
        lines.append(
            f"├ Average buy price: <code>{portfolio.average_buy_price:,.4f} USDC</code>"
        )
        lines.append(f"└ Total cost: <code>{portfolio.total_cost:,.2f} USDC</code>")
        lines.append("")

    lines.append("──────────────────")
    lines.append(f"💰 <b>Total invested:</b> <code>{total_invested:,.2f} USDC</code>")

    return "\n".join(lines).rstrip()


# Returns history message text
def get_history_message(context: ContextTypes.DEFAULT_TYPE) -> str:
    service = context.application.bot_data["transaction_service"]
    transactions = service.get_all_transactions()

    if not transactions:
        return "📜 Transaction history is empty."

    lines = ["📜 <b>Transaction history:</b>", ""]

    for transaction in transactions[:10]:
        emoji = (
            "🟢"
            if transaction.transaction_type.value == "BUY"
            else "🔴"
        )

        # Transaction symbol supporting <, > and other special html chars
        symbol_esc = escape(transaction.symbol)

        lines.append(
            f"{emoji} <b>{symbol_esc}</b> "
            f"· {transaction.transaction_type.value}"
        )
        lines.append(f"| <i>{transaction.created_at.strftime('%Y-%m-%d %H:%M')}</i>")
        lines.append(f"| Quantity: <code>{transaction.quantity} {symbol_esc}</code>")
        lines.append(f"| Price per unit: <code>{transaction.price} USDC</code>")
        lines.append(f"| Transaction value: {(transaction.quantity * transaction.price):,.2f} USDC")
        lines.append("")

    message = "\n".join(lines).rstrip()

    if len(transactions) > 10:
        message += "\n\n<i>Showing the 10 most recent transactions.</i>"

    return message


# Sub menus for every coin
def get_symbol_history_message(context: ContextTypes.DEFAULT_TYPE, symbol: str) -> str:
    service = context.application.bot_data["transaction_service"]
    transactions = [
        tx
        for tx in service.get_all_transactions()
        if tx.symbol == symbol
    ]

    if not transactions:
        return f"📜 No transactions found for {escape(symbol)}."

    portfolio = service.get_portfolio(symbol)
    holdings = portfolio.quantity

    lines = [
        f"📜 <b>Full history: {escape(symbol)}</b>",
        f"🏦 Remaining: {holdings} {escape(symbol)}",
        ""
    ]

    for tx in transactions:
        emoji = (
            "🟢"
            if tx.transaction_type.value == "BUY"
            else "🔴"
        )

        # Transaction symbol supporting <, > and other special html chars
        symbol_esc = escape(tx.symbol)

        lines.append(
            f"{emoji} <b>{symbol_esc}</b> "
            f"· {tx.transaction_type.value}"
        )
        lines.append(f"| <i>{tx.created_at.strftime('%Y-%m-%d %H:%M')}</i>")
        lines.append(f"| Quantity: <code>{tx.quantity} {symbol_esc}</code>")
        lines.append(f"| Price per unit: <code>{tx.price} USDC</code>")
        lines.append(f"| Transaction value: {(tx.quantity * tx.price):,.2f} USDC")
        lines.append("")

    return "\n".join(lines).rstrip()


# Show transaction to delete details
def get_delete_confirmation_message(context: ContextTypes.DEFAULT_TYPE, transaction_id: UUID) -> str | None:
    service = context.application.bot_data["transaction_service"]

    transaction = next(
        (
            tx for tx in service.get_all_transactions()
            if tx.id == transaction_id
        ),
        None,
    )

    if transaction is None:
        return None

    symbol = escape(transaction.symbol)
    emoji = "🟢" if transaction.transaction_type.value == "BUY" else "🔴"

    return (
        "⚠️ <b>Delete this transaction?</b>\n\n"
        f"{emoji} <b>{transaction.transaction_type.value} · {symbol}</b>\n"
        f"Date: <i>{transaction.created_at.strftime('%Y-%m-%d %H:%M')}</i>\n"
        f"Quantity: <code>{transaction.quantity} {symbol}</code>\n"
        f"Price: <code>{transaction.price:,.4f} USDC</code>\n"
        f"Value: <code>{transaction.value:,.2f} USDC</code>\n\n"
        "This action cannot be undone."
    )

# -----------------------------------------------------------------
# --------------------- MENU BUTTONS HANDLERS ---------------------
# -----------------------------------------------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    if query is None or update.effective_user is None:
        return

    allowed_user_id = context.application.bot_data["telegram_user_id"]

    if update.effective_user.id != allowed_user_id:
        await query.answer("Access denied.", show_alert=True)
        return

    await query.answer()
    reply_markup = main_menu_keyboard()

    # --------------------------
    # ---- PORTFOLIO BUTTON ----
    if query.data == "portfolio":
        message = get_portfolio_messages(context)

    # ---- HISTORY MENU BUTTON ----
    elif query.data == "history":
        message = (
            "📜 <b>Transaction history</b>\n\n"
            "Choose what you want to see:"
        )

        # Last 10 transactions or specified coin all transactions
        reply_markup = history_menu_keyboard()

    # ---- HISTORY LAST 10 BUTTONS ----
    elif query.data == "history_last":
        message = get_history_message(context)
        reply_markup = history_last_keyboard()

    # ---- HISTORY BTNs FOR ALL COINS ----
    elif query.data == "history_full":
        keyboard = history_symbols_keyboard(context)

        if keyboard is None:
            message = "📜 Transaction history is empty."
            reply_markup = history_back_keyboard()

        else:
            message = "🪙 <b>Choose a cryptocurrency:</b>"
            reply_markup = keyboard

    # ---- FULL HISTORY FOR SPECIFIED COIN ----
    elif query.data.startswith("history_symbol:"):
        symbol = query.data.split(":", 1)[1]

        message = get_symbol_history_message(context, symbol)
        reply_markup = history_back_keyboard()

    # ---- SENDs NEW MESSAGE WITH HISTORY MENU ----
    elif query.data == "history_back":
        message = (
            "📜 <b>Transaction history</b>\n\n"
            "Choose what you want to see:"
        )

        # Last 10 transactions or specified coin all transactions
        reply_markup = history_menu_keyboard()

    # ---- BUY & SELL BUTTON ----
    elif query.data in ("buy", "sell"):
        cmd = query.data  # buy or sell

        emoji = (
            "➕"
            if cmd == "buy"
            else "➖"
        )

        lines = [f"{emoji} <b>Place a {cmd.upper()} order</b>", ""]

        lines.append(f"Use: <code>/{cmd} SYMBOL QUANTITY PRICE</code>")
        lines.append("")
        lines.append(f"Example: <code>/{cmd} BTC 0.025 90000</code>")
        lines.append(f"<i>(i.e.: you {'bought' if cmd == 'buy' else 'sold'} 0.025 BTC at a price of 90,000 USDC per 1 BTC)</i>")

        message = "\n".join(lines).rstrip()

        # Add new buttons to fill command or exit to main menu
        reply_markup = fill_command_keyboard(cmd)

    # ---- Last 10 txs DELETE MENU ----
    elif query.data == "history_delete_menu":
        service = context.application.bot_data["transaction_service"]
        transactions = service.get_all_transactions()

        if not transactions:
            message = "📜 Transaction history is empty."
            reply_markup = history_last_keyboard()
        else:
            message = (
                "🗑 <b>Choose a transaction to delete</b>\n\n"
                "Select the transaction you want to remove:"
            )
            reply_markup = history_transactions_keyboard(context)

    # ---- ASK FOR DELETE CONFIRMATION ----
    elif query.data.startswith("delete_tx:"):
        transaction_id = UUID(query.data.split(":", 1)[1])

        message = get_delete_confirmation_message(
            context,
            transaction_id,
        )

        if message is None:
            message = "⚠️ Transaction not found."
            reply_markup = history_transactions_keyboard(context)
        else:
            reply_markup = delete_confirmation_keyboard(transaction_id)

    # ---- CONFIRM DELETE ----
    elif query.data.startswith("confirm_delete:"):
        transaction_id = UUID(query.data.split(":", 1)[1])
        service = context.application.bot_data["transaction_service"]

        try:
            deleted = service.delete_transaction(transaction_id)

            if deleted:
                message = (
                    "✅ <b>Transaction deleted successfully.</b>\n\n"
                    + get_history_message(context)
                )
                reply_markup = history_transactions_keyboard(context)
            else:
                message = "⚠️ Transaction not found."
                reply_markup = history_transactions_keyboard(context)

        except ValueError as exc:
            message = (
                "❌ <b>Transaction cannot be deleted.</b>\n\n"
                f"{escape(str(exc))}\n\n"
                "The transaction history has not been changed."
            )
            reply_markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 Back to recent history",
                        callback_data=f"cancel_delete:{transaction_id}",
                    )
                ]
            ])

        except sqlite3.Error:
            logger.exception("Database error while deleting transaction")
            message = (
                "⚠️ <b>Database error.</b>\n\n"
                "The transaction could not be deleted."
            )
            reply_markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 Back to recent history",
                        callback_data=f"cancel_delete:{transaction_id}",
                    )
                ]
            ])

    # ---- CANCEL DELETE ----
    elif query.data.startswith("cancel_delete:"):
        message = get_history_message(context)
        reply_markup = history_transactions_keyboard(context)

    elif query.data == "start":
        await start(update, context)
        return

    else:
        messages = {
            "who": "Bot created by me.",
        }

        message = messages.get(query.data, "Unknown option.")

    if query.message:
        if(
            query.data in (
                "history_last",
                "history_full",
                "history_back",
                "history_delete_menu",
            )
            or query.data.startswith("history_symbol:")
            or query.data.startswith("delete_tx:")
            or query.data.startswith("confirm_delete:")
            or query.data.startswith("cancel_delete:")
        ):
            # Edit message only in History MENU & Delete tx MENU
            try:
                await query.edit_message_text(
                    text=message,
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )
            except BadRequest as exc:
                if "Message is not modified" not in str(exc):
                    raise

        else:
            # Other buttons sends NEW message
            await query.message.reply_text(message, parse_mode="HTML", reply_markup=reply_markup)


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

    operation = operation.upper()

    if operation not in ("BUY", "SELL"):
        await update.message.reply_text("⚠️ Unknown transaction type.")
        return

    # Add new buttons to fill or exit to main menu
    reply_markup = fill_command_keyboard(operation.lower())

    if len(context.args) != 3:
        await update.message.reply_text(
            f"❌ <b>Invalid /{operation.lower()} command format</b>\n\n"
            f"Use: <code>/{operation.lower()} SYMBOL QUANTITY PRICE</code>\n\n"
            f"Example: <code>/{operation.lower()} BTC 0.025 90000</code>\n"
            f"<i>(i.e.: you {'bought' if operation.lower() == 'buy' else 'sold'} 0.025 BTC at a price of 90,000 USDC per 1 BTC)</i>",
            parse_mode="HTML",
            reply_markup=reply_markup
        )
        return

    symbol, quantity_text, price_text = context.args

    if not symbol.strip():
        await update.message.reply_text(
            "⚠️ Symbol cannot be empty.",
            reply_markup=reply_markup
        )
        return

    try:
        quantity = Decimal(quantity_text.replace(",", "."))
        price = Decimal(price_text.replace(",", "."))
    except (InvalidOperation, ValueError):
        await update.message.reply_text(
            "⚠️ Quantity and price must be valid numbers.",
            reply_markup=reply_markup
        )
        return

    if not quantity.is_finite() or not price.is_finite():
        await update.message.reply_text(
            "⚠️ Quantity and price must be finite numbers.",
            reply_markup=reply_markup
        )
        return

    if quantity <= 0 or price <= 0:
        await update.message.reply_text(
            "⚠️ Quantity and price must be greater than zero.",
            reply_markup=reply_markup
        )
        return

    service = context.application.bot_data["transaction_service"]

    try:
        if operation == "BUY":
            transaction = service.add_buy(symbol, quantity, price)
        elif operation == "SELL":
            transaction = service.add_sell(symbol, quantity, price)

    except (ValueError, TypeError) as exc:
        await update.message.reply_text(
            f"⚠️ Transaction not saved: {exc}",
            reply_markup=reply_markup
        )
        return

    except sqlite3.Error:
        logger.exception("Database error while saving transaction")
        await update.message.reply_text(
            "⚠️ Database error. The transaction could not be saved.",
            reply_markup=reply_markup
        )
        return

    portfolio = service.get_portfolio(symbol)

    action = 'Bought' if transaction.transaction_type.value == 'BUY' else 'Sold'
    symbol_esc = escape(transaction.symbol)

    await update.message.reply_text(
        f"✅ <b>Transaction {transaction.transaction_type.value} for {symbol_esc} saved successfully!</b>\n"
        f"• Type: {'🟢' if transaction.transaction_type.value == 'BUY' else '🔴'} {transaction.transaction_type.value}\n"
        f"• {action}: {transaction.quantity} {symbol_esc} "
        f"at {transaction.price} USDC\n"
        f"• Total: {transaction.value} USDC"
        "\n\n"
        f"📊 Actual portfolio for {symbol_esc}:\n"
        f"• Quantity: {portfolio.quantity} {symbol_esc}\n"
        f"• Average buy price: {portfolio.average_buy_price:,.4f} USDC\n"
        f"• Total cost: {portfolio.total_cost:,.2f} USDC\n",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard()
    )


# Handle messages with @bot_name before /buy and /sell
async def handle_inline_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None or update.message is None:
        return

    text = update.message.text.strip()
    bot_username = f"@{context.bot.username}"

    # Checking if message starts with @bot_name
    if text.lower().startswith(bot_username.lower()):
        clean_text = text[len(bot_username):].strip()  # leaves only "/buy ..."
        parts = clean_text.split()

        if not parts:
            return

        command = parts[0].lower()
        context.args = parts[1:]

        if command == "/buy":
            await _handle_transaction_command(update, context, "BUY")
        elif command == "/sell":
            await _handle_transaction_command(update, context, "SELL")


async def portfolio_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None or update.message is None:
        return

    allowed_user_id = context.application.bot_data["telegram_user_id"]

    if update.effective_user.id != allowed_user_id:
        await update.message.reply_text("Access denied.")
        return

    message = get_portfolio_messages(context)

    await update.message.reply_text(message, parse_mode="HTML", reply_markup=main_menu_keyboard())


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None or update.message is None:
        return

    allowed_user_id = context.application.bot_data["telegram_user_id"]

    if update.effective_user.id != allowed_user_id:
        await update.message.reply_text("Access denied.")
        return

    message = (
        "📜 <b>Transaction history</b>\n\n"
        "Choose what you want to see:"
    )

    await update.message.reply_text(message, parse_mode="HTML", reply_markup=history_menu_keyboard())
