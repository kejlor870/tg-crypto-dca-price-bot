import os
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

if __name__ == "__main__":
    print("Hello World")
