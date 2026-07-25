"""
Barcha maxfiy sozlamalar shu yerda, atrof-muhit o'zgaruvchilari (environment
variables) orqali o'qiladi. Hech qachon TOKEN yoki ID'larni to'g'ridan-to'g'ri
kodga yozib qo'ymang — ular .env faylida turadi va .env hech qachon GitHub'ga
yuklanmaydi (.gitignore'da).
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- Telegram ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# Admin chat ID'lari. Bir nechta admin bo'lsa, vergul bilan ajrating:
#   ADMIN_CHAT_IDS=5079059516,123456789
# Moslik uchun eski bitta qiymatli ADMIN_CHAT_ID ham qo'llab-quvvatlanadi.
_admin_raw = os.environ.get("ADMIN_CHAT_IDS", "") or os.environ.get("ADMIN_CHAT_ID", "")
ADMIN_CHAT_IDS = [x.strip() for x in _admin_raw.split(",") if x.strip()]
# "Asosiy" admin (birinchi ID) — ba'zi joylarda yagona qiymat kerak bo'lsa ishlatiladi.
ADMIN_CHAT_ID = ADMIN_CHAT_IDS[0] if ADMIN_CHAT_IDS else ""

CHANNEL_ID = os.environ.get("CHANNEL_ID", "")              # maxfiy admin kanal ID'si
BOT_USERNAME = os.environ.get("BOT_USERNAME", "")          # masalan: cryptospot3_bot (@ belgisisiz)

# Webhook maxfiy tokeni: Telegram har bir /webhook so'rovida shu qiymatni
# "X-Telegram-Bot-Api-Secret-Token" sarlavhasida yuboradi. Shu bilan begona
# odam soxta yangilik (masalan soxta admin buyrug'i) yubora olmaydi.
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# --- To'lov ma'lumotlari (kripto hamyon) ---
# MUHIM: hozircha bo'sh. Abdulloh USDT (TRC20/BEP20) hamyon manzilini bersa, shu yerga yoziladi.
USDT_WALLET_ADDRESS = os.environ.get("USDT_WALLET_ADDRESS", "HALI_KIRITILMAGAN")
USDT_NETWORK = os.environ.get("USDT_NETWORK", "TRC20")  # yoki BEP20, TON va h.k.

# --- Tariflar (narxlar shu yerda markazlashgan, frontend bilan mos bo'lishi kerak) ---
PRICING = {
    "cs3_vip": {"name": "CS3% Execution Lab — VIP", "price": 119},
    "cs3_premium": {"name": "CS3% Execution Lab — Premium", "price": 249},
    "vip3_1m": {"name": "VIP 3% — 1 oylik obuna", "price": 10},
    "vip3_3m": {"name": "VIP 3% — 3 oylik obuna", "price": 25},
}

# --- Database ---
DB_PATH = os.environ.get("DB_PATH", "bot_data.db")
