import os
import time
from datetime import datetime
import requests
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

BOT_TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "0"))
DATA_FILE = os.path.join(BASE_DIR, "zakupy.txt")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


def send_message(chat_id, text):
    requests.post(
        f"{TELEGRAM_API_URL}/sendMessage",
        json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
        timeout=10,
    )


def send_backup_file(chat_id):
    if not os.path.exists(DATA_FILE):
        send_message(chat_id, "Brak zapisanych transakcji do wysłania.")
        return
    with open(DATA_FILE, "rb") as f:
        requests.post(
            f"{TELEGRAM_API_URL}/sendDocument",
            data={"chat_id": chat_id, "caption": "Kopia zapasowa: zakupy.txt"},
            files={"document": ("zakupy.txt", f)},
            timeout=15,
        )


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
                transactions.append({
                    "date": parts[0],
                    "type": parts[1],
                    "symbol": parts[2].upper(),
                    "amount": float(parts[3]),
                    "price": float(parts[4]),
                })
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
        portfolio[sym]["avg_price"] = (
            portfolio[sym]["cost_basis"] / amt if amt > 1e-12 else 0.0
        )
    return portfolio


def parse_number(val):
    return float(val.replace(",", "."))


def handle_message(message):
    user_id = message.get("from", {}).get("id")
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "").strip()

    if user_id != ALLOWED_USER_ID:
        print(f"Zignorowano wiadomość od nieznanego ID: {user_id}")
        return

    if not text.startswith("/"):
        return

    parts = text.split()
    command = parts[0].lower().split("@")[0]

    if command in ("/start", "/help"):
        help_text = (
            "*Dostępne komendy:*\n"
            "`/buy BTC 0.05 92000` – zapisuje zakup (symbol, ilość, cena za 1 szt. w USDC)\n"
            "`/sell BTC 0.02 98000` – zapisuje sprzedaż części pozycji\n"
            "`/portfolio` lub `/list` – podsumowanie portfela i średnich cen\n"
            "`/history BTC` – historia wpisów dla danej kryptowaluty\n"
            "`/undo` – cofa ostatnią zapisaną operację\n"
            "`/backup` – wysyła plik `zakupy.txt` na czat"
        )
        send_message(chat_id, help_text)

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
            send_message(chat_id, "Ilość i cena muszą być poprawnymi liczbami większymi od zera.")
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
        send_backup_file(chat_id)

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
            send_message(chat_id, "Ilość i cena muszą być poprawnymi liczbami.")
            return

        transactions = load_transactions()
        portfolio = calculate_portfolio(transactions)
        owned = portfolio.get(symbol, {}).get("amount", 0.0)

        if amount > owned + 1e-12:
            send_message(chat_id, f"Nie masz tyle {symbol} w portfelu (posiadasz: `{owned:g}`).")
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
        send_backup_file(chat_id)

    elif command in ("/portfolio", "/list"):
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

    elif command == "/history":
        if len(parts) != 2:
            send_message(chat_id, "Podaj symbol kryptowaluty, np. `/history BTC`")
            return

        symbol = parts[1].upper()
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

    elif command == "/undo":
        if not os.path.exists(DATA_FILE):
            send_message(chat_id, "Brak wpisów do cofnięcia.")
            return

        with open(DATA_FILE, "r", encoding="utf-8") as f:
            lines = [l for l in f.readlines() if l.strip()]

        if not lines:
            send_message(chat_id, "Brak wpisów do cofnięcia.")
            return

        removed = lines.pop().strip()
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines)

        send_message(chat_id, f"↩️ *Cofnięto ostatni wpis:*\n`{removed}`")

    elif command == "/backup":
        send_backup_file(chat_id)

    else:
        send_message(chat_id, "Nieznana komenda. Wpisz `/help`, aby zobaczyć listę.")


def run_polling():
    if not BOT_TOKEN or not ALLOWED_USER_ID:
        print("BŁĄD: Uzupełnij BOT_TOKEN i ALLOWED_USER_ID w pliku .env!")
        return

    # Upewniamy się, że żaden stary webhook nie blokuje lokalnego pollingu
    requests.get(f"{TELEGRAM_API_URL}/deleteWebhook", timeout=10)
    print("Bot uruchomiony lokalnie! Oczekuję na komendy w Telegramie...")

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
        except Exception as e:
            print(f"Błąd połączenia: {e}")
            time.sleep(3)


if __name__ == "__main__":
    run_polling()
