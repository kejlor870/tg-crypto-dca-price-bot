import os
import time
from datetime import datetime
import requests
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
_raw_user_id = os.getenv("ALLOWED_USER_ID", "0").strip()
try:
    ALLOWED_USER_ID = int(_raw_user_id)
except ValueError:
    ALLOWED_USER_ID = 0

DATA_FILE = os.path.join(BASE_DIR, "zakupy.txt")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


def get_main_keyboard():
    return {
        "inline_keyboard": [
            [
                {"text": "💼 Portfolio", "callback_data": "cmd_portfolio"},
                {"text": "📜 Historia", "callback_data": "cmd_history_menu"},
            ],
            [
                {"text": "➕ Zakup / Sprzedaż", "callback_data": "cmd_trade_help"},
                {"text": "↩️ Cofnij wpis", "callback_data": "cmd_undo"},
            ],
            [
                {"text": "💾 Pobierz Backup (.txt)", "callback_data": "cmd_backup"},
            ],
        ]
    }


def send_message(chat_id, text, reply_markup=None, parse_mode="Markdown"):
    if reply_markup is None:
        reply_markup = get_main_keyboard()

    payload = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": reply_markup,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode

    try:
        resp = requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload, timeout=10)
        if not resp.ok and parse_mode:
            # Jeśli Markdown wywoła błąd formatowania w Telegramie, wyślij jako zwykły tekst
            payload.pop("parse_mode", None)
            requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload, timeout=10)
    except requests.RequestException as e:
        print(f"Błąd wysyłania wiadomości: {e}")


def answer_callback(callback_id, text=""):
    try:
        requests.post(
            f"{TELEGRAM_API_URL}/answerCallbackQuery",
            json={"callback_query_id": callback_id, "text": text},
            timeout=5,
        )
    except requests.RequestException as e:
        print(f"Błąd answerCallbackQuery: {e}")


def send_backup_file(chat_id):
    if not os.path.exists(DATA_FILE):
        send_message(chat_id, "Brak zapisanych transakcji do wysłania.")
        return
    try:
        with open(DATA_FILE, "rb") as f:
            requests.post(
                f"{TELEGRAM_API_URL}/sendDocument",
                data={"chat_id": chat_id, "caption": "💾 Kopia zapasowa: zakupy.txt"},
                files={"document": ("zakupy.txt", f)},
                timeout=15,
            )
    except requests.RequestException as e:
        print(f"Błąd wysyłania pliku backup: {e}")
        send_message(chat_id, "Nie udało się wysłać pliku kopii zapasowej.")


def load_transactions():
    transactions = []
    if not os.path.exists(DATA_FILE):
        return transactions
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("|")
            if len(parts) == 5:
                try:
                    transactions.append({
                        "date": parts[0],
                        "type": parts[1],
                        "symbol": parts[2].upper(),
                        "amount": float(parts[3]),
                        "price": float(parts[4]),
                    })
                except ValueError:
                    print(f"Pominięto uszkodzony wiersz w {DATA_FILE}: {line}")
    return transactions


def save_transaction(tx_type, symbol, amount, price):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    line = f"{now}|{tx_type}|{symbol.upper()}|{amount}|{price}\n"
    with open(DATA_FILE, "a", encoding="utf-8") as f:
        f.write(line)


def calculate_portfolio(transactions):
    portfolio = {}
    for tx in transactions:
        sym = tx["symbol"]
        if sym not in portfolio:
            portfolio[sym] = {"amount": 0.0, "cost_basis": 0.0}

        if tx["type"] == "BUY":
            portfolio[sym]["amount"] += tx["amount"]
            portfolio[sym]["cost_basis"] += tx["amount"] * tx["price"]
        elif tx["type"] == "SELL":
            current_amt = portfolio[sym]["amount"]
            if current_amt > 0:
                avg_price = portfolio[sym]["cost_basis"] / current_amt
                sold_amt = min(tx["amount"], current_amt)
                portfolio[sym]["amount"] -= sold_amt
                portfolio[sym]["cost_basis"] -= sold_amt * avg_price

    for sym in portfolio:
        amt = portfolio[sym]["amount"]
        if amt <= 1e-12:
            portfolio[sym]["amount"] = 0.0
            portfolio[sym]["cost_basis"] = 0.0
            portfolio[sym]["avg_price"] = 0.0
        else:
            portfolio[sym]["avg_price"] = portfolio[sym]["cost_basis"] / amt
    return portfolio


def parse_number(val):
    num = float(val.replace(",", ".").strip())
    if num != num or num in (float("inf"), float("-inf")):
        raise ValueError("Niepoprawna liczba")
    return num


def action_portfolio(chat_id):
    transactions = load_transactions()
    if not transactions:
        send_message(chat_id, "Twój portfel jest pusty. Dodaj pierwszy zakup przez `/buy`.")
        return

    portfolio = calculate_portfolio(transactions)
    lines = ["💼 *Twoje zestawienie krypto:*\n"]
    total_capital = 0.0

    for sym, data in sorted(portfolio.items()):
        if data["amount"] > 1e-12:
            total_capital += data["cost_basis"]
            lines.append(
                f"*{sym}*\n"
                f"• Ilość: `{data['amount']:g}`\n"
                f"• Średnia cena: `{data['avg_price']:,.4f} USDC`\n"
                f"• Włożony kapitał: `{data['cost_basis']:,.2f} USDC`\n"
            )

    if len(lines) == 1:
        send_message(chat_id, "Brak aktywnych pozycji w portfelu.")
        return

    lines.append(f"💰 *Łącznie zainwestowano:* `{total_capital:,.2f} USDC`")
    send_message(chat_id, "\n".join(lines))


def action_history_menu(chat_id):
    transactions = load_transactions()
    if not transactions:
        send_message(chat_id, "Brak zapisanych transakcji.")
        return

    symbols = sorted({tx["symbol"] for tx in transactions})
    buttons = [
        [{"text": f"📜 Historia {sym}", "callback_data": f"hist_{sym}"}]
        for sym in symbols
    ]
    buttons.append([{"text": "🔙 Wróć do menu", "callback_data": "cmd_help"}])

    send_message(
        chat_id,
        "Wybierz kryptowalutę, której historię chcesz zobaczyć:",
        reply_markup={"inline_keyboard": buttons},
    )


def action_history_symbol(chat_id, symbol):
    symbol = symbol.upper()
    transactions = [tx for tx in load_transactions() if tx["symbol"] == symbol]
    if not transactions:
        send_message(chat_id, f"Brak historii transakcji dla `{symbol}`.")
        return

    lines = [f"📜 *Historia operacji dla {symbol}:*\n"]
    for tx in transactions[-20:]:
        icon = "🟢" if tx["type"] == "BUY" else "🔴"
        lines.append(
            f"{icon} `{tx['date']}` | {tx['type']} `{tx['amount']:g}` po `{tx['price']:,.4f} USDC`"
        )
    send_message(chat_id, "\n".join(lines))


def action_undo(chat_id):
    if not os.path.exists(DATA_FILE):
        send_message(chat_id, "Brak wpisów do cofnięcia.")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        lines = [line for line in f.readlines() if line.strip()]

    if not lines:
        send_message(chat_id, "Brak wpisów do cofnięcia.")
        return

    removed = lines.pop().strip()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)

    send_message(chat_id, f"↩️ *Cofnięto ostatni wpis:*\n`{removed}`")


def action_help(chat_id):
    help_text = (
        "*Panel zarządzania portfelem krypto*\n\n"
        "Kliknij przycisk poniżej lub wpisz komendę:\n"
        "• `/buy BTC 0.05 92000` – zapisuje zakup\n"
        "• `/sell BTC 0.02 98000` – zapisuje sprzedaż\n"
        "• `/portfolio` – stan portfela i średnie ceny\n"
        "• `/history BTC` – historia wpisów\n"
        "• `/undo` – cofa ostatni wpis\n"
        "• `/backup` – wysyła plik `zakupy.txt`"
    )
    send_message(chat_id, help_text)


def handle_callback(callback_query):
    callback_id = callback_query.get("id")
    user_id = callback_query.get("from", {}).get("id")
    message = callback_query.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    data = callback_query.get("data", "")

    if user_id != ALLOWED_USER_ID or not chat_id:
        return

    answer_callback(callback_id)

    if data == "cmd_portfolio":
        action_portfolio(chat_id)
    elif data == "cmd_history_menu":
        action_history_menu(chat_id)
    elif data.startswith("hist_"):
        symbol = data.removeprefix("hist_")
        action_history_symbol(chat_id, symbol)
    elif data == "cmd_undo":
        action_undo(chat_id)
    elif data == "cmd_backup":
        send_backup_file(chat_id)
    elif data == "cmd_trade_help":
        send_message(
            chat_id,
            "Aby zapisać transakcję, wyślij wiadomość w formacie:\n\n"
            "🟢 *Zakup:* `/buy BTC 0.05 92000`\n"
            "🔴 *Sprzedaż:* `/sell BTC 0.02 98000`\n"
            "_(Symbol, ilość monety, cena za 1 szt. w USDC)_",
        )
    elif data == "cmd_help":
        action_help(chat_id)


def handle_message(message):
    user_id = message.get("from", {}).get("id")
    chat_id = message.get("chat", {}).get("id")
    text = (message.get("text") or "").strip()

    if user_id != ALLOWED_USER_ID or not chat_id:
        return

    if not text.startswith("/"):
        return

    parts = text.split()
    command = parts[0].lower().split("@")[0]

    if command in ("/start", "/help"):
        action_help(chat_id)

    elif command == "/buy":
        if len(parts) != 4:
            send_message(chat_id, "Błędny format. Użyj:\n`/buy BTC 0.05 92000`")
            return
        try:
            symbol = parts[1].upper()
            amount = parse_number(parts[2])
            price = parse_number(parts[3])
            if amount <= 0 or price < 0:
                raise ValueError
        except ValueError:
            send_message(chat_id, "Ilość musi być większa od zera, a cena nieujemna.")
            return

        save_transaction("BUY", symbol, amount, price)
        portfolio = calculate_portfolio(load_transactions())
        stats = portfolio[symbol]
        total_spent = amount * price

        reply = (
            f"✅ *Zapisano zakup {symbol}*\n"
            f"• Kupiono: `{amount:g} {symbol}` po `{price:,.4f} USDC`\n"
            f"• Wartość zlecenia: `{total_spent:,.2f} USDC`\n\n"
            f"📊 *Aktualny stan {symbol}:*\n"
            f"• Łączna ilość: `{stats['amount']:g} {symbol}`\n"
            f"• Średnia cena kupna: `{stats['avg_price']:,.4f} USDC`\n"
            f"• Zainwestowany kapitał: `{stats['cost_basis']:,.2f} USDC`"
        )
        send_message(chat_id, reply)

    elif command == "/sell":
        if len(parts) != 4:
            send_message(chat_id, "Błędny format. Użyj:\n`/sell BTC 0.02 98000`")
            return
        try:
            symbol = parts[1].upper()
            amount = parse_number(parts[2])
            price = parse_number(parts[3])
            if amount <= 0 or price < 0:
                raise ValueError
        except ValueError:
            send_message(chat_id, "Ilość musi być większa od zera, a cena nieujemna.")
            return

        transactions = load_transactions()
        portfolio = calculate_portfolio(transactions)
        owned = portfolio.get(symbol, {}).get("amount", 0.0)
        if amount > owned + 1e-12:
            send_message(chat_id, f"Nie masz tyle `{symbol}` w portfelu (posiadasz: `{owned:g}`).")
            return

        save_transaction("SELL", symbol, amount, price)
        updated = calculate_portfolio(load_transactions())[symbol]
        reply = (
            f"🔻 *Zapisano sprzedaż {symbol}*\n"
            f"• Sprzedano: `{amount:g} {symbol}` po `{price:,.4f} USDC`\n"
            f"• Pozostało w portfelu: `{updated['amount']:g} {symbol}`\n"
            f"• Średnia cena zakupu pozostałych: `{updated['avg_price']:,.4f} USDC`"
        )
        send_message(chat_id, reply)

    elif command in ("/portfolio", "/list"):
        action_portfolio(chat_id)

    elif command == "/history":
        if len(parts) != 2:
            action_history_menu(chat_id)
            return
        action_history_symbol(chat_id, parts[1])

    elif command == "/undo":
        action_undo(chat_id)

    elif command == "/backup":
        send_backup_file(chat_id)

    else:
        send_message(chat_id, "Nieznana komenda. Wybierz opcję z przycisków poniżej:")


def run_polling():
    if not BOT_TOKEN or not ALLOWED_USER_ID:
        print("BŁĄD: Uzupełnij BOT_TOKEN i ALLOWED_USER_ID w pliku .env!")
        return

    try:
        requests.get(f"{TELEGRAM_API_URL}/deleteWebhook", timeout=10)
    except requests.RequestException as e:
        print(f"Uwaga – nie udało się usunąć webhooka: {e}")

    print("Bot uruchomiony lokalnie z menu przycisków! Oczekuję na akcje...")
    offset = 0
    while True:
        try:
            resp = requests.get(
                f"{TELEGRAM_API_URL}/getUpdates",
                params={"offset": offset, "timeout": 30},
                timeout=35,
            ).json()
            for update in resp.get("result", []):
                offset = update["update_id"] + 1
                if "message" in update:
                    handle_message(update["message"])
                elif "callback_query" in update:
                    handle_callback(update["callback_query"])
        except Exception as e:
            print(f"Błąd połączenia: {e}")
            time.sleep(3)


if __name__ == "__main__":
    run_polling()