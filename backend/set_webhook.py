"""
Render.com'ga deploy qilingandan so'ng, bu skriptni BIR MARTA ishga tushiring:

    python set_webhook.py https://sizning-render-domeningiz.onrender.com

Bu Telegram'ga: "yangi xabarlar kelganda shu URL'ga POST qil" deb aytadi.
"""
import sys

import config
from telegram_api import set_webhook, delete_webhook

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Foydalanish: python set_webhook.py https://domeningiz.onrender.com")
        sys.exit(1)

    base_url = sys.argv[1].rstrip("/")
    webhook_url = f"{base_url}/webhook"

    delete_webhook()
    # WEBHOOK_SECRET .env'da bo'lsa, Telegram'ga ham shu tokenni beramiz —
    # keyin backend har bir so'rovni shu token bo'yicha tekshiradi.
    result = set_webhook(webhook_url, config.WEBHOOK_SECRET or None)
    print(result)
