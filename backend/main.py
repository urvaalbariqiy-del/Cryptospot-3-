"""
Cryptospot 3% — ANKETA boti backend (@CRYPTO3FOIZBOT).

Voronka: anketa (sayt) -> admin tasdiqlaydi (tugma yoki Reply) -> saytda tarif
tanlash ochiladi -> to'lov manejer botda.

Bu bot faqat anketa/tasdiqlash uchun (VIP 3% / to'lov / community mavjud
MANEJER botda). Webhook rejimida ishlaydi.
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

app = FastAPI(title="Cryptospot 3% anketa bot backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    storage.init_db()


# ============================================================
# MATNLAR
# ============================================================

REGISTERED_TEXT = (
    "✅ <b>Tayyor!</b>\n\n"
    "Ro'yxatdan o'tdingiz. Endi <b>saytga qayting</b> va anketani to'ldiring — "
    "admin ko'rib chiqib tasdiqlaydi, so'ng saytda tarif tanlash ochiladi."
)

APPROVED_USER_TEXT = (
    "✅ <b>Tabriklaymiz!</b>\n\n"
    "Anketangiz <b>tasdiqlandi</b>. Endi saytga qayting va o'zingizga mos "
    "<b>tarifni tanlang</b> — to'lov va kirish manejer bot orqali amalga oshadi."
)

ADMIN_INFO_TEXT = (
    "🛠 <b>Anketa boti</b>\n\n"
    "Sayt anketalari shu chatga keladi. Tasdiqlash uchun anketa ostidagi "
    "<b>✅ Tasdiqlash</b> tugmasini bosing yoki xabarga <b>Reply</b> qilib yozing "
    "(Reply ham tasdiq hisoblanadi va foydalanuvchiga yetkaziladi)."
)


def back_to_site_keyboard():
    if not config.SITE_URL:
        return None
    return {"inline_keyboard": [[{"text": "🌐 Saytga qaytish", "url": config.SITE_URL}]]}


def approve_keyboard(user_chat_id):
    return {"inline_keyboard": [[
        {"text": "✅ Tasdiqlash", "callback_data": f"approve:{user_chat_id}"}
    ]]}


# ============================================================
# TELEGRAM WEBHOOK
# ============================================================

@app.post("/webhook")
async def telegram_webhook(request: Request):
    if config.WEBHOOK_SECRET:
        token = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if token != config.WEBHOOK_SECRET:
            return Response(status_code=403)

    try:
        data = await request.json()
    except Exception:
        return {"ok": True}

    try:
        if "callback_query" in data:
            await handle_callback_query(data["callback_query"])
        elif "message" in data:
            await handle_message(data["message"])
    except Exception:
        traceback.print_exc()

    return {"ok": True}


def is_admin(chat_id) -> bool:
    return str(chat_id) in {str(a) for a in config.ADMIN_CHAT_IDS}


def approve_user(user_chat_id):
    """Foydalanuvchini tasdiqlaydi va unga xabar beradi."""
    storage.set_setting(f"status:{user_chat_id}", "approved")
    try:
        send_message(int(user_chat_id), APPROVED_USER_TEXT, reply_markup=back_to_site_keyboard())
    except Exception:
        pass


async def handle_callback_query(cq: dict):
    from_chat = cq["message"]["chat"]["id"]
    data = cq.get("data", "")

    if data.startswith("approve:") and is_admin(from_chat):
        target = data.split(":", 1)[1]
        approve_user(target)
        answer_callback_query(cq["id"], text="Tasdiqlandi ✅")
        send_message(from_chat, "✅ Foydalanuvchi tasdiqlandi — saytda unga tarif tanlash ochildi.")
        return

    answer_callback_query(cq["id"])


async def handle_message(msg: dict):
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")
    admin = is_admin(chat_id)

    # 1) Admin javob (reply) -> foydalanuvchiga yetkazish + tasdiq (Reply = tasdiq)
    if admin and msg.get("reply_to_message"):
        replied_id = msg["reply_to_message"]["message_id"]
        user_chat_id = storage.get_user_for_admin_message(chat_id, replied_id)
        if user_chat_id:
            if text:
                send_message(user_chat_id, text, parse_mode=None)
                # admin javobini saytda ham ko'rsatish uchun saqlaymiz
                storage.set_setting(f"reply:{user_chat_id}", text)
            else:
                copy_message(user_chat_id, chat_id, msg["message_id"])
            approve_user(user_chat_id)  # Reply ham tasdiq
        return

    # 2) /start
    if text.startswith("/start"):
        if admin:
            send_message(chat_id, ADMIN_INFO_TEXT)
            return
        parts = text.split(maxsplit=1)
        payload = parts[1].strip() if len(parts) > 1 else ""
        if payload:
            storage.register_session(payload, chat_id)
        send_message(chat_id, REGISTERED_TEXT, reply_markup=back_to_site_keyboard())
        return

    # 3) Admin oddiy xabar -> e'tiborsiz
    if admin:
        return

    # 4) Oddiy foydalanuvchi xabari -> har bir adminga forward + relay
    for admin_id in config.ADMIN_CHAT_IDS:
        fwd = forward_message(admin_id, chat_id, msg["message_id"])
        if fwd.get("ok"):
            storage.save_relay(admin_id, fwd["result"]["message_id"], chat_id)


# ============================================================
# SAYT UCHUN API
# ============================================================

@app.get("/api/check-registration/{session_id}")
async def check_registration(session_id: str):
    chat_id = storage.get_chat_id_for_session(session_id)
    return {"registered": chat_id is not None}


@app.get("/api/status/{session_id}")
async def user_status(session_id: str):
    """Sayt shu endpoint orqali holatni kuzatadi:
    registered -> anketa formasi ochiladi
    approved   -> tarif tanlash ochiladi (admin tasdiqlagan)
    admin_message -> admin javobini saytda ko'rsatish uchun."""
    chat_id = storage.get_chat_id_for_session(session_id)
    if not chat_id:
        return {"registered": False, "approved": False, "admin_message": ""}
    approved = storage.get_setting(f"status:{chat_id}") == "approved"
    admin_message = storage.get_setting(f"reply:{chat_id}") or ""
    return {"registered": True, "approved": approved, "admin_message": admin_message}


@app.post("/api/survey")
async def submit_survey(request: Request):
    try:
        body = await request.json()
    except Exception:
        return {"ok": False, "error": "bad_request"}

    session_id = body.get("session_id", "")
    chat_id = storage.get_chat_id_for_session(session_id)
    if not chat_id:
        return {"ok": False, "error": "not_registered"}

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
        "Tasdiqlash uchun quyidagi tugmani bosing yoki shu xabarga <b>Reply</b> qiling."
    )

    kb = approve_keyboard(chat_id)
    sent_any = False
    for admin_id in config.ADMIN_CHAT_IDS:
        result = send_message(admin_id, text, reply_markup=kb)
        if result.get("ok"):
            storage.save_relay(admin_id, result["result"]["message_id"], chat_id)
            sent_any = True

    return {"ok": True} if sent_any else {"ok": False, "error": "telegram_send_failed"}


@app.get("/")
async def health():
    return {"status": "ok", "service": "cryptospot3-anketa-bot-backend"}
