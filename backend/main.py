"""
CS3% Execution Lab / Cryptospot 3% — Telegram bot + anketa API backend.

Ishlash mantig'i (qisqacha):
  1. Sayt "Ro'yxatdan o'tish" tugmasi orqali foydalanuvchini
     t.me/<bot>?start=<session_id> ga yo'naltiradi.
  2. Foydalanuvchi botda /start bosadi -> biz session_id'ni uning chat_id'siga
     bog'laymiz (storage.register_session).
  3. Sayt /api/check-registration/<session_id> orqali buni tekshiradi va
     anketa qismini ochadi.
  4. Anketa /api/survey ga POST qilinadi -> biz uni chiroyli formatlab admin
     chatga yuboramiz va shu xabar ID'sini foydalanuvchi chat_id bilan
     bog'laymiz (storage.save_relay) — shunda admin shu xabarga "Reply"
     qilib yozsa, bot buni avtomatik foydalanuvchiga yetkazadi.
  5. Har qanday oddiy foydalanuvchi botga yozgan xabari (savol, chek rasmi va
     h.k.) ham xuddi shunday admin chatga forward qilinadi va relay jadvaliga
     yoziladi — shu bilan admin va foydalanuvchi bot orqali ikki tomonlama
     "operator" suhbatini olib boradi.
  6. VIP 3% uchun to'g'ridan-to'g'ri tarif tanlash va to'lov ko'rsatmasi bot
     ichida amalga oshadi (inline tugmalar orqali).

Bu fayl webhook rejimida ishlaydi (Telegram yangiliklarni shu endpointga
yuboradi). Polling emas — Render.com kabi doimiy ishlaydigan web-service uchun
webhook to'g'ri yechim.
"""
import html
import traceback

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

import config
import storage
from telegram_api import (
    send_message,
    forward_message,
    copy_message,
    answer_callback_query,
)

app = FastAPI(title="Cryptospot 3% bot backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # xohlasangiz bu yerga faqat o'z domeningizni yozing
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    storage.init_db()


# ============================================================
# TELEGRAM MATNLARI
# ============================================================

WELCOME_TEXT = (
    "Assalomu alaykum! 👋\n\n"
    "<b>Cryptospot 3%</b> rasmiy botiga xush kelibsiz.\n"
    "Quyidagilardan birini tanlang:"
)

EXECUTION_LAB_TEXT = (
    "📋 <b>CS3% Execution Lab</b>\n\n"
    "Anketani veb-saytimizda to'ldiring — bu yerga qaytib kelish shart emas, "
    "botga ro'yxatdan o'tganingiz saytdagi anketa qismini avtomatik ochadi.\n\n"
    "Anketani to'ldirgach, admin javoblaringizni ko'rib chiqib, shu bot orqali "
    "siz bilan bog'lanadi."
)

VIP3_INTRO_TEXT = (
    "📈 <b>VIP 3% — signal va strategiya kanali</b>\n\n"
    "Obuna muddatini tanlang:"
)

MYCOMMUNITY_TEXT = (
    "👥 <b>My Community</b>\n\n"
    "Bu jamoaga to'g'ridan-to'g'ri qo'shilish mavjud emas — u faqat "
    "<b>CS3% Execution Lab</b> dasturining <b>Premium tarifi</b> orqali ochiladi.\n\n"
    "Premium tarif haqida batafsil ma'lumot uchun saytimizdagi \"Tariflar\" "
    "bo'limiga qarang."
)


def main_menu_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📋 CS3% Execution Lab — Anketa", "callback_data": "menu_execution_lab"}],
            [{"text": "📈 VIP 3% ga qo'shilish", "callback_data": "menu_vip3"}],
            [{"text": "👥 My Community haqida", "callback_data": "menu_mycommunity"}],
        ]
    }


def vip3_tariff_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "1 oylik — $10", "callback_data": "buy_vip3_1m"}],
            [{"text": "3 oylik — $25", "callback_data": "buy_vip3_3m"}],
        ]
    }


def admin_menu_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "💳 Hamyonni ko'rish", "callback_data": "admin_wallet"}],
            [{"text": "✏️ Hamyonni o'zgartirish", "callback_data": "admin_setwallet"}],
        ]
    }


def get_wallet_info():
    """Admin bot orqali /setwallet bilan kiritgan hamyonni qaytaradi;
    agar hali kiritilmagan bo'lsa, config'dagi standart qiymatga tushadi."""
    address = storage.get_setting("usdt_wallet_address", config.USDT_WALLET_ADDRESS)
    network = storage.get_setting("usdt_wallet_network", config.USDT_NETWORK)
    return address, network


def payment_instructions(tariff_key: str, order_id: int) -> str:
    tariff = config.PRICING.get(tariff_key)
    name = tariff["name"] if tariff else tariff_key
    price = tariff["price"] if tariff else "?"
    address, network = get_wallet_info()
    return (
        f"✅ Siz tanladingiz: <b>{name}</b> — ${price}\n\n"
        f"💳 To'lovni quyidagi hamyonga o'tkazing:\n"
        f"<code>{address}</code>\n"
        f"Tarmoq: <b>{network}</b> (USDT)\n\n"
        f"To'lovni amalga oshirgach, <b>chek rasmini shu botga yuboring</b>. "
        f"Admin tekshirib, tasdiqlagach sizga kirish huquqi beriladi.\n\n"
        f"🔖 Buyurtma raqami: #{order_id}"
    )


# ============================================================
# TELEGRAM WEBHOOK
# ============================================================

@app.post("/webhook")
async def telegram_webhook(request: Request):
    # Xavfsizlik: WEBHOOK_SECRET o'rnatilgan bo'lsa, so'rov haqiqatan Telegram'dan
    # kelganini tekshiramiz. Aks holda begona odam soxta yangilik (masalan soxta
    # admin buyrug'i /setwallet) yuborib, tizimni aldashi mumkin edi.
    if config.WEBHOOK_SECRET:
        token = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if token != config.WEBHOOK_SECRET:
            return Response(status_code=403)

    try:
        data = await request.json()
    except Exception:
        return {"ok": True}

    # Har qanday handler xatosi Render Logs'da ko'rinishi va Telegram'ga 500
    # qaytmasligi uchun (aks holda Telegram so'rovni qayta-qayta yuboraveradi).
    try:
        if "callback_query" in data:
            await handle_callback_query(data["callback_query"])
        elif "message" in data:
            await handle_message(data["message"])
    except Exception:
        traceback.print_exc()

    return {"ok": True}


def is_admin(chat_id) -> bool:
    """chat_id adminlardan biri ekanligini tekshiradi (bir yoki bir nechta admin)."""
    return str(chat_id) in {str(a) for a in config.ADMIN_CHAT_IDS}


async def handle_message(msg: dict):
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")
    admin = is_admin(chat_id)

    # 0) Admin uchun maxsus buyruqlar (hamyonni bot orqali kiritish/ko'rish)
    if admin and text.startswith("/"):
        handled = await handle_admin_command(chat_id, text)
        if handled:
            return

    # 1) Admin javob (reply) yozganida -> tegishli foydalanuvchiga yetkazish.
    #    Relay shu admin chatidagi xabar ID'si bo'yicha qidiriladi.
    if admin and msg.get("reply_to_message"):
        replied_id = msg["reply_to_message"]["message_id"]
        user_chat_id = storage.get_user_for_admin_message(chat_id, replied_id)
        if user_chat_id:
            if text:
                # Admin erkin yozgan matn — HTML formatlashsiz yuboramiz, aks holda
                # matnda < yoki & bo'lsa Telegram xato berib, xabar yetmay qolardi.
                send_message(user_chat_id, text, parse_mode=None)
            else:
                # rasm/fayl bo'lsa — copyMessage orqali yuboramiz (forward emas),
                # shunda foydalanuvchida "admin'dan forward qilindi" ko'rinmaydi.
                copy_message(user_chat_id, chat_id, msg["message_id"])
        return

    # 1b) Admin "✏️ Hamyonni o'zgartirish" tugmasini bosgach — keyingi (buyruq
    #     bo'lmagan) xabari yangi hamyon sifatida qabul qilinadi.
    if admin and text and not text.startswith("/") and \
            storage.get_setting(f"admin_state:{chat_id}") == "awaiting_wallet":
        storage.set_setting(f"admin_state:{chat_id}", "")  # holatni tozalaymiz
        parts = text.split()
        if not parts:
            send_message(chat_id, "Bekor qilindi.", reply_markup=admin_menu_keyboard())
            return
        address = parts[0]
        network = parts[1] if len(parts) > 1 else "TRC20"
        storage.set_setting("usdt_wallet_address", address)
        storage.set_setting("usdt_wallet_network", network)
        send_message(
            chat_id,
            f"✅ To'lov hamyoni yangilandi:\n<code>{address}</code>\nTarmoq: <b>{network}</b>",
            reply_markup=admin_menu_keyboard(),
        )
        return

    # 2) /start (registratsiya)
    if text.startswith("/start"):
        if admin:
            send_message(chat_id, ADMIN_PANEL_TEXT, reply_markup=admin_menu_keyboard())
            return
        parts = text.split(maxsplit=1)
        payload = parts[1].strip() if len(parts) > 1 else ""
        if payload:
            storage.register_session(payload, chat_id)
        send_message(chat_id, WELCOME_TEXT, reply_markup=main_menu_keyboard())
        return

    # 3) Admin panelda oddiy (reply bo'lmagan) xabar yozsa — e'tiborsiz qoldiramiz
    if admin:
        return

    # 4) Oddiy foydalanuvchi xabari (savol, chek rasmi va h.k.) -> HAR BIR admin
    #    chatga forward qilinadi va har biri uchun alohida relay yoziladi.
    for admin_id in config.ADMIN_CHAT_IDS:
        fwd = forward_message(admin_id, chat_id, msg["message_id"])
        if fwd.get("ok"):
            admin_message_id = fwd["result"]["message_id"]
            storage.save_relay(admin_id, admin_message_id, chat_id)


ADMIN_PANEL_TEXT = (
    "🛠 <b>Admin panel</b>\n\n"
    "Quyidagi tugmalardan foydalaning:"
)

ADMIN_HELP_TEXT = (
    "🛠 <b>Admin panel</b>\n\n"
    "Tugmalar orqali boshqaring (pastdagi menyu), yoki matnli buyruqlar:\n"
    "<code>/wallet</code> — hozirgi to'lov hamyonini ko'rsatadi\n"
    "<code>/setwallet MANZIL TARMOQ</code> — to'lov hamyonini yangilaydi\n"
    "Masalan: <code>/setwallet TXo1234...abcd TRC20</code>\n\n"
    "<code>/admin_help</code> — shu ro'yxatni qayta ko'rsatadi"
)


async def handle_admin_command(chat_id, text: str) -> bool:
    """Admin uchun maxsus buyruqlarni qayta ishlaydi.
    Return: True — buyruq sifatida qayta ishlandi (boshqa logikaga o'tmasin),
            False — bu oddiy buyruq emas, davom etilsin (masalan /start)."""

    if text.startswith("/admin_help"):
        send_message(chat_id, ADMIN_HELP_TEXT, reply_markup=admin_menu_keyboard())
        return True

    if text.startswith("/wallet"):
        address, network = get_wallet_info()
        send_message(
            chat_id,
            f"💳 Hozirgi to'lov hamyoni:\n<code>{address}</code>\nTarmoq: <b>{network}</b>\n\n"
            f"O'zgartirish uchun: <code>/setwallet MANZIL TARMOQ</code>",
        )
        return True

    if text.startswith("/setwallet"):
        parts = text.split()
        # parts[0] = "/setwallet"
        if len(parts) < 2:
            send_message(
                chat_id,
                "Foydalanish: <code>/setwallet MANZIL TARMOQ</code>\n"
                "Masalan: <code>/setwallet TXo1234...abcd TRC20</code>",
            )
            return True
        address = parts[1]
        network = parts[2] if len(parts) > 2 else "TRC20"
        storage.set_setting("usdt_wallet_address", address)
        storage.set_setting("usdt_wallet_network", network)
        send_message(
            chat_id,
            f"✅ To'lov hamyoni yangilandi:\n<code>{address}</code>\nTarmoq: <b>{network}</b>",
        )
        return True

    return False


async def handle_callback_query(cq: dict):
    chat_id = cq["message"]["chat"]["id"]
    action = cq.get("data", "")
    answer_callback_query(cq["id"])

    # --- Admin panel tugmalari ---
    if action in ("admin_wallet", "admin_setwallet"):
        if not is_admin(chat_id):
            return
        if action == "admin_wallet":
            address, network = get_wallet_info()
            send_message(
                chat_id,
                f"💳 Hozirgi to'lov hamyoni:\n<code>{address}</code>\nTarmoq: <b>{network}</b>",
                reply_markup=admin_menu_keyboard(),
            )
        else:  # admin_setwallet — keyingi xabarni hamyon sifatida kutamiz
            storage.set_setting(f"admin_state:{chat_id}", "awaiting_wallet")
            send_message(
                chat_id,
                "✏️ Yangi hamyon manzili va tarmog'ini <b>bitta xabarda</b> yuboring.\n"
                "Masalan:\n<code>TXo1234abcd TRC20</code>\n\n"
                "(Tarmoqni yozmasangiz, standart <b>TRC20</b> olinadi.)",
            )
        return

    if action == "menu_execution_lab":
        send_message(chat_id, EXECUTION_LAB_TEXT)
    elif action == "menu_vip3":
        send_message(chat_id, VIP3_INTRO_TEXT, reply_markup=vip3_tariff_keyboard())
    elif action == "menu_mycommunity":
        send_message(chat_id, MYCOMMUNITY_TEXT)
    elif action in ("buy_vip3_1m", "buy_vip3_3m"):
        tariff_key = action.replace("buy_", "")
        order_id = storage.create_order(chat_id, tariff_key)
        send_message(chat_id, payment_instructions(tariff_key, order_id))


# ============================================================
# SAYT UCHUN API
# ============================================================

@app.get("/api/check-registration/{session_id}")
async def check_registration(session_id: str):
    chat_id = storage.get_chat_id_for_session(session_id)
    return {"registered": chat_id is not None}


@app.post("/api/survey")
async def submit_survey(request: Request):
    body = await request.json()
    session_id = body.get("session_id", "")
    chat_id = storage.get_chat_id_for_session(session_id)

    if not chat_id:
        return {"ok": False, "error": "not_registered"}

    # Foydalanuvchi kiritgan qiymatlarni HTML uchun xavfsizlaymiz — aks holda ism
    # yoki matnda < & belgilari bo'lsa, Telegram HTML tahlilida xato beradi.
    def esc(key):
        return html.escape(str(body.get(key, "-")))

    text = (
        "🆕 <b>Yangi anketa — CS3% Execution Lab</b>\n"
        f"👤 Ism: {esc('name')}\n"
        f"🎂 Yosh: {esc('age')}\n"
        f"📈 Tajriba: {esc('years')} yil\n"
        f"💰 Balans: {esc('balance')}\n"
        f"📉 Zarar: {esc('loss')}\n"
        f"💭 Xato sababi: {esc('cause')}\n\n"
        "↩️ Foydalanuvchi bilan gaplashish uchun shu xabarga <b>Reply</b> qiling."
    )
    # Anketa har bir adminga yuboriladi; har biri "Reply" orqali javob bera olishi
    # uchun alohida relay yoziladi.
    sent_any = False
    for admin_id in config.ADMIN_CHAT_IDS:
        result = send_message(admin_id, text)
        if result.get("ok"):
            storage.save_relay(admin_id, result["result"]["message_id"], chat_id)
            sent_any = True

    if sent_any:
        return {"ok": True}

    return {"ok": False, "error": "telegram_send_failed"}


@app.get("/")
async def health():
    return {"status": "ok", "service": "cryptospot3-bot-backend"}
