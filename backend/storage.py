"""
Juda oddiy SQLite qatlami. Uchta jadval:

sessions   — saytdagi anonim tashrif buyuruvchini ("session_id") Telegram
             chat_id bilan bog'laydi (bot /start bosilgandan keyin).
relay      — admin chatiga yuborilgan/forward qilingan xabar ID'sini asl
             foydalanuvchi chat_id bilan bog'laydi, shunda admin "Reply"
             qilganda bot qayerga yuborishni biladi.
orders     — foydalanuvchi tanlagan tarif va holati (kutilmoqda / tasdiqlandi).
"""
import sqlite3
import time
from contextlib import contextmanager

from config import DB_PATH


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                chat_id INTEGER NOT NULL,
                created_at INTEGER NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS relay (
                admin_message_id INTEGER PRIMARY KEY,
                user_chat_id INTEGER NOT NULL,
                created_at INTEGER NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                tariff TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at INTEGER NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at INTEGER NOT NULL
            )
        """)
        conn.commit()


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


# ---------- sessions ----------

def register_session(session_id: str, chat_id: int):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO sessions (session_id, chat_id, created_at) VALUES (?, ?, ?)",
            (session_id, chat_id, int(time.time())),
        )
        conn.commit()


def get_chat_id_for_session(session_id: str):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT chat_id FROM sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
        return row[0] if row else None


# ---------- relay (admin <-> user ikki tomonlama xabar almashish) ----------

def save_relay(admin_message_id: int, user_chat_id: int):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO relay (admin_message_id, user_chat_id, created_at) VALUES (?, ?, ?)",
            (admin_message_id, user_chat_id, int(time.time())),
        )
        conn.commit()


def get_user_for_admin_message(admin_message_id: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT user_chat_id FROM relay WHERE admin_message_id = ?", (admin_message_id,)
        ).fetchone()
        return row[0] if row else None


# ---------- orders ----------

def create_order(chat_id: int, tariff: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO orders (chat_id, tariff, status, created_at) VALUES (?, ?, 'pending', ?)",
            (chat_id, tariff, int(time.time())),
        )
        conn.commit()
        return cur.lastrowid


def set_order_status(order_id: int, status: str):
    with get_conn() as conn:
        conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        conn.commit()


# ---------- settings (masalan: admin bot orqali kiritgan to'lov hamyoni) ----------

def set_setting(key: str, value: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
            (key, value, int(time.time())),
        )
        conn.commit()


def get_setting(key: str, default=None):
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row[0] if row else default
