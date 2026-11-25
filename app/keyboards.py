from telegram import InlineKeyboardMarkup, InlineKeyboardButton


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
