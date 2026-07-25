"""
Cryptospot 3% — ANKETA boti backend (@CRYPTO3FOIZBOT).

Bu bot faqat sayt anketasi uchun (VIP 3% / to'lov / community mavjud MANEJER
botda — bu bot ularga aralashmaydi). Vazifasi:

  1. Sayt "Botda ro'yxatdan o'tish" tugmasi orqali foydalanuvchini
     t.me/<bot>?start=<session_id> ga yo'naltiradi.
  2. Foydalanuvchi /start bosadi -> session_id uning chat_id'siga bog'lanadi
     (storage.register_session) va botga "saytga qayting" deb aytiladi.
  3. Sayt /api/check-registration/<session_id> orqali buni tekshiradi va
     anketa formasini ochadi.
  4. Anketa /api/survey ga POST qilinadi -> admin(lar)ga yuboriladi va shu
     xabar ID'si foydalanuvchi chat_id bilan bog'lanadi (relay) — admin
     "Reply" qilib yozsa, bot uni avtomatik foydalanuvchiga yetkazadi.
  5. Foydalanuvchi botga yozgan har qanday xabar ham admin(lar)ga forward
     qilinadi va relay'ga yoziladi (ikki tomonlama "operator" suhbati).

Webhook rejimida ishlaydi.
"""
import html
import traceback

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

import config
import storage
from telegram_api import send_message, forward_message, copy_message

app = FastAPI(title="Cryptospot 3% anketa bot backend")

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
# MATNLAR
# ============================================================

REGISTERED_TEXT = (
    "✅ <b>Tayyor!</b>\n\n"
    "Ro'yxatdan o'tdingiz. Endi <b>saytga qayting</b> va anketani to'ldiring — "
    "javoblaringiz shu bot orqali adminga yetkaziladi va admin siz bilan "
    "bog'lanadi."
)

ADMIN_INFO_TEXT = (
    "🛠 <b>Anketa boti</b>\n\n"
    "Sayt anketalari va foydalanuvchi xabarlari shu chatga keladi.\n"
    "Foydalanuvchiga javob berish uchun kelgan xabarga <b>Reply</b> qiling — "
    "bot uni avtomatik yetkazadi."
)


def back_to_site_keyboard():
    """SITE_URL o'rnatilgan bo'lsa 'Saytga qaytish' tugmasini beradi."""
    if not config.SITE_URL:
        return None
    return {"inline_keyboard": [[{"text": "🌐 Saytga qaytish", "url": config.SITE_URL}]]}


# ============================================================
# TELEGRAM WEBHOOK
# ============================================================

@app.post("/webhook")
async def telegram_webhook(request: Request):
    # Xavfsizlik: WEBHOOK_SECRET o'rnatilgan bo'lsa, so'rov haqiqatan Telegram'dan
    # kelganini tekshiramiz.
    if config.WEBHOOK_SECRET:
        token = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if token != config.WEBHOOK_SECRET:
            return Response(status_code=403)

    try:
        data = await request.json()
    except Exception:
        return {"ok": True}

    # Handler xatosi Render Logs'da ko'rinsin, Telegram'ga 500 qaytmasin.
    try:
        if "message" in data:
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

    # 1) Admin javob (reply) yozganida -> tegishli foydalanuvchiga yetkazish.
    if admin and msg.get("reply_to_message"):
        replied_id = msg["reply_to_message"]["message_id"]
        user_chat_id = storage.get_user_for_admin_message(chat_id, replied_id)
        if user_chat_id:
            if text:
                # Admin erkin matni — HTML formatlashsiz (< yoki & xato bermasin).
                send_message(user_chat_id, text, parse_mode=None)
            else:
                # rasm/fayl — copyMessage (forward emas, admin sizib chiqmaydi).
                copy_message(user_chat_id, chat_id, msg["message_id"])
        return

    # 2) /start — ro'yxatdan o'tkazish (yoki admin uchun qisqa ma'lumot)
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

    # 3) Admin oddiy (reply bo'lmagan) xabar yozsa — e'tiborsiz qoldiramiz
    if admin:
        return

    # 4) Oddiy foydalanuvchi xabari -> HAR BIR adminga forward + relay
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

    # Foydalanuvchi kiritgan qiymatlarni HTML uchun xavfsizlaymiz.
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

    sent_any = False
    for admin_id in config.ADMIN_CHAT_IDS:
        result = send_message(admin_id, text)
        if result.get("ok"):
            storage.save_relay(admin_id, result["result"]["message_id"], chat_id)
            sent_any = True

    return {"ok": True} if sent_any else {"ok": False, "error": "telegram_send_failed"}


@app.get("/")
async def health():
    return {"status": "ok", "service": "cryptospot3-anketa-bot-backend"}
