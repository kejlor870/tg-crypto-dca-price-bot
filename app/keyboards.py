from __future__ import annotations

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes


def main_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("📊 Portfolio", callback_data="portfolio"),
            InlineKeyboardButton("📜 History", callback_data="history")
        ],
        [
            InlineKeyboardButton("➕ Buy", callback_data="buy"),
            InlineKeyboardButton("➖ Sell", callback_data="sell")
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


def fill_command_keyboard(cmd: str) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text="🏠 Main menu",
                callback_data="start",
            ),
            InlineKeyboardButton(
                text=f"✍️ Fill /{cmd}",
                switch_inline_query_current_chat=f"/{cmd} "
            )
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


def history_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🕒 Last 10 transactions",
                callback_data="history_last",
            )
        ],
        [
            InlineKeyboardButton(
                "🪙 Full history by crypto",
                callback_data="history_full",
            )
        ],
        [
            InlineKeyboardButton(
                "🏠 Main menu",
                callback_data="start",
            )
        ],
    ])


def history_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔙 Back to history",
                callback_data="history",
            )
        ],
        [
            InlineKeyboardButton(
                "🏠 Main menu",
                callback_data="start",
            )
        ],
    ])


def history_symbols_keyboard(context: ContextTypes.DEFAULT_TYPE) -> InlineKeyboardMarkup | None:
    service = context.application.bot_data["transaction_service"]
    transactions = service.get_all_transactions()

    symbols = sorted({tx.symbol for tx in transactions})

    if not symbols:
        return None

    buttons = [
        [
            InlineKeyboardButton(
                f"🪙 {symbol}",
                callback_data=f"history_symbol:{symbol}",
            )
        ]
        for symbol in symbols
    ]

    buttons.append([
        InlineKeyboardButton(
            "🔙 Back to history",
            callback_data="history",
        )
    ])

    buttons.append([
        InlineKeyboardButton(
            "🏠 Main menu",
            callback_data="start",
        )
    ])

    return InlineKeyboardMarkup(buttons)
