"""
Telegram Bot API'ga so'rov yuboruvchi kichik wrapper. Faqat `requests`
kutubxonasidan foydalanadi — qo'shimcha og'ir kutubxona shart emas.
"""
import requests

from config import TELEGRAM_API


def send_message(chat_id, text, reply_markup=None, parse_mode="HTML"):
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = reply_markup
    r = requests.post(f"{TELEGRAM_API}/sendMessage", json=payload, timeout=10)
    return r.json()


def forward_message(chat_id, from_chat_id, message_id):
    payload = {"chat_id": chat_id, "from_chat_id": from_chat_id, "message_id": message_id}
    r = requests.post(f"{TELEGRAM_API}/forwardMessage", json=payload, timeout=10)
    return r.json()


def copy_message(chat_id, from_chat_id, message_id, caption=None):
    payload = {"chat_id": chat_id, "from_chat_id": from_chat_id, "message_id": message_id}
    if caption:
        payload["caption"] = caption
    r = requests.post(f"{TELEGRAM_API}/copyMessage", json=payload, timeout=10)
    return r.json()


def answer_callback_query(callback_query_id, text=None):
    payload = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text
    r = requests.post(f"{TELEGRAM_API}/answerCallbackQuery", json=payload, timeout=10)
    return r.json()


def set_webhook(url, secret_token=None):
    payload = {"url": url}
    if secret_token:
        # Telegram bu tokenni har bir webhook so'rovida qaytarib yuboradi,
        # shunda backend so'rov haqiqatan Telegram'dan kelganini tekshira oladi.
        payload["secret_token"] = secret_token
    r = requests.post(f"{TELEGRAM_API}/setWebhook", json=payload, timeout=10)
    return r.json()


def delete_webhook():
    r = requests.post(f"{TELEGRAM_API}/deleteWebhook", timeout=10)
    return r.json()
