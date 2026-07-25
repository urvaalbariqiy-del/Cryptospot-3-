# Cryptospot 3% — Bot Backend

Bu backend uchta vazifani bajaradi:
1. Telegram botni boshqaradi (ro'yxatdan o'tish, menyu, VIP 3% to'lov oqimi).
2. Sayt anketasini qabul qilib, admin chatga yuboradi.
3. Admin va foydalanuvchi o'rtasida ikki tomonlama xabar almashishni ("Reply" orqali) ta'minlaydi.

## 1. Render.com'ga joylash

1. Bu `backend/` papkani alohida GitHub repo qiling (yoki asosiy reponing bir qismi sifatida).
   **MUHIM**: `.env` faylini hech qachon GitHub'ga qo'shmang — `.gitignore` allaqachon uni chetlab o'tadi.
2. [render.com](https://render.com) da **New + → Web Service** tanlang, shu repo'ni ulang.
3. Sozlamalar:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. **Environment** bo'limida quyidagi o'zgaruvchilarni qo'lda kiriting (Render dashboard'ida, `.env` fayl emas):
   - `BOT_TOKEN`
   - `ADMIN_CHAT_ID`
   - `CHANNEL_ID`
   - `BOT_USERNAME`
   - `WEBHOOK_SECRET` — istalgan uzun tasodifiy satr (masalan `openssl rand -hex 16` chiqargan qiymat). Webhook xavfsizligi uchun; tavsiya etiladi.
   - `USDT_WALLET_ADDRESS`
   - `USDT_NETWORK`
5. Deploy tugagach, Render sizga URL beradi, masalan: `https://cs3-backend.onrender.com`

## 2. Webhookni ulash (bir marta)

Lokal kompyuteringizda (yoki Render "Shell" bo'limida):

```bash
pip install -r requirements.txt
python set_webhook.py https://cs3-backend.onrender.com
```

Bu Telegram'ga "yangi xabarlar shu yerga kelsin" deb aytadi. Muvaffaqiyatli bo'lsa
`{"ok": true, "result": true, ...}` javobini ko'rasiz.

**Xavfsizlik eslatmasi:** agar `WEBHOOK_SECRET` o'rnatgan bo'lsangiz, `set_webhook.py`
uni avtomatik Telegram'ga uzatadi va backend har bir `/webhook` so'rovini shu token
bo'yicha tekshiradi. Shu bilan begona odam soxta yangilik (masalan soxta admin
`/setwallet` buyrug'i) yuborib, to'lov hamyonini o'zgartira olmaydi. Shuning uchun
`WEBHOOK_SECRET`ni o'rnatganingizdan **keyin** `set_webhook.py`ni qayta ishga tushiring.

## 3. Saytni ulash

`assets/js/config.js` faylida:
```js
apiBaseUrl: "https://cs3-backend.onrender.com",
telegramBotUsername: "sizning_bot_username",
```

## 4. To'lov hamyonini kiritish (endi bot orqali ham mumkin!)

Admin (`ADMIN_CHAT_ID`da ko'rsatilgan chat) botga `/start` bossa, admin buyruqlari ro'yxati chiqadi:

- `/wallet` — hozirgi to'lov hamyonini ko'rsatadi
- `/setwallet MANZIL TARMOQ` — to'lov hamyonini yangilaydi, masalan:
  `/setwallet TXo1234...abcd TRC20`
- `/admin_help` — buyruqlar ro'yxatini qayta ko'rsatadi

Bu orqali kiritilgan hamyon darhol ishlatila boshlaydi — kodni o'zgartirish yoki
qayta deploy qilish shart emas. Agar hali hech narsa kiritilmagan bo'lsa, backend
`.env`dagi `USDT_WALLET_ADDRESS` qiymatiga tushadi (standart holat).

## 5. Botning ishlash tartibi (qisqacha)

- Foydalanuvchi sayt orqali botga `/start <session_id>` bilan kiradi → ro'yxatdan o'tadi.
- Bot asosiy menyu ko'rsatadi: CS3% Execution Lab anketasi / VIP 3% / My Community haqida.
- VIP 3% tanlansa — tarif (1 oy $10 / 3 oy $25) va to'lov hamyoni ko'rsatiladi.
- Foydalanuvchi to'lov chekini botga yuborsa — bu avtomatik admin chatga forward bo'ladi.
- Admin forward qilingan xabarga **Reply** qilib yozsa — bot buni avtomatik o'sha foydalanuvchiga yetkazadi (ikki tomonlama suhbat).
- Sayt anketasi to'ldirilsa — xuddi shunday admin chatga tushadi, admin Reply orqali javob beradi.

## 6. Ma'lumotlar bazasi haqida eslatma

Hozir oddiy SQLite fayl (`bot_data.db`) ishlatiladi. Render'ning bepul tarifida
disk doimiy emas — deploy qilinganda fayl tozalanishi mumkin. Agar bu muhim
bo'lsa (masalan uzoq muddat saqlanishi kerak bo'lsa), keyinroq buni ARZON'da
ishlatilayotgan Neon/PostgreSQL bazasiga ulab qo'yishimiz mumkin — xohlasangiz
buni ham qilib beraman.

## 7. Lokal test qilish (ixtiyoriy)

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Bu http://localhost:8000 da ishga tushadi, lekin Telegram webhook uchun ochiq
internet manzili kerak (masalan `ngrok` orqali), shuning uchun to'liq test uchun
Render'ga joylash tavsiya etiladi.
