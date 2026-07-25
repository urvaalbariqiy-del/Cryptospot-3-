# Cryptospot 3% — Landing sahifa + Bot backend

Bu papkada butun loyiha bor: sayt (frontend) va Telegram bot (backend).

## Tuzilma

```
/                       ← sayt (statik HTML/CSS/JS, build kerak emas)
  index.html
  assets/css/main.css
  assets/js/main.js      ← til (UZ/RU), tema, anketa/ro'yxat logikasi
  assets/js/config.js    ← backend URL va bot username shu yerga yoziladi
  assets/img/            ← logotiplar, asoschi fotosi
  README.md              ← saytni ochish/deploy qilish yo'riqnomasi

backend/                ← Telegram bot + anketa API (Python/FastAPI)
  main.py                ← asosiy mantiq (webhook, menyular, anketa, to'lov)
  config.py              ← .env'dan o'qiladigan sozlamalar
  storage.py              ← SQLite (sessiyalar, admin-user xabar bog'lanishi, buyurtmalar, hamyon)
  telegram_api.py         ← Telegram Bot API bilan ishlash
  set_webhook.py          ← deploy'dan keyin bir marta ishga tushiriladigan skript
  requirements.txt
  .env                    ← HAQIQIY token/ID'lar bilan to'ldirilgan (GitHub'ga yubormang!)
  README.md               ← Render.com'ga deploy qilish yo'riqnomasi
```

## Claude Code'da davom ettirish uchun

Agar bu papkani Claude Code'ga (yoki boshqa muhitga) o'tkazsangiz:

1. **Avval `backend/README.md`ni o'qing** — u yerda Render.com'ga deploy qilish
   bosqichlari bor (build/start buyruqlari, environment o'zgaruvchilar,
   webhook o'rnatish).
2. Backend deploy bo'lgach, uning URL'ini `assets/js/config.js` ichidagi
   `apiBaseUrl` ga yozing, `telegramBotUsername` ni ham to'ldiring.
3. Saytni istalgan statik hosting'ga (Hostinger + Dokploy, Vercel, Netlify va
   h.k.) joylashtirsangiz bo'ladi — build qadam kerak emas, `index.html`ni
   ochish kifoya.
4. To'lov hamyonini backend qayta deploy qilmasdan ham botning o'zidan
   (`/setwallet MANZIL TARMOQ` buyrug'i orqali, admin sifatida) kiritish mumkin.

## Muhim eslatmalar

- `backend/.env` faylida haqiqiy bot TOKEN, admin ID va kanal ID bor — bu fayl
  `.gitignore`da, hech qachon ochiq repo'ga tushmaydi.
- Frontend endi Telegram tokenini o'zida saqlamaydi — barcha maxfiy narsalar
  faqat backend serverida turadi.
- SQLite (`bot_data.db`) — sodda, fayl-asosli baza. Agar kelajakda buni
  Neon/PostgreSQL'ga ko'chirish kerak bo'lsa (ARZON'dagidek), so'rang — buni
  ham qurib beraman.
