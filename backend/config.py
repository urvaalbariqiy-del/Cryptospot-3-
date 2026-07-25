"""
Maxfiy sozlamalar environment o'zgaruvchilaridan o'qiladi. TOKEN/ID'larni
hech qachon kodga yozmang — ular .env (yoki Render Environment) da turadi.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- Telegram (ANKETA boti @CRYPTO3FOIZBOT) ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# Admin chat ID'lari. Bir nechta admin bo'lsa, vergul bilan ajrating:
#   ADMIN_CHAT_IDS=5079059516,123456789
# Moslik uchun eski bitta qiymatli ADMIN_CHAT_ID ham qo'llab-quvvatlanadi.
_admin_raw = os.environ.get("ADMIN_CHAT_IDS", "") or os.environ.get("ADMIN_CHAT_ID", "")
ADMIN_CHAT_IDS = [x.strip() for x in _admin_raw.split(",") if x.strip()]
ADMIN_CHAT_ID = ADMIN_CHAT_IDS[0] if ADMIN_CHAT_IDS else ""

# Webhook maxfiy tokeni — Telegram har bir /webhook so'rovida shuni yuboradi,
# shu bilan begona odam soxta yangilik yubora olmaydi.
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")

# Sayt manzili (ixtiyoriy) — /start javobidagi "Saytga qaytish" tugmasi uchun.
# Masalan: https://cryptospot-3.vercel.app
SITE_URL = os.environ.get("SITE_URL", "")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# --- Database ---
DB_PATH = os.environ.get("DB_PATH", "bot_data.db")
