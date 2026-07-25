# CS3% Execution Lab — Landing sahifa

Bu sahifa toza HTML/CSS/JS bilan qurilgan (build qadam kerak emas), shuning uchun
uni ochish yoki serverga joylashtirish juda oddiy.

## Ochish (lokal)
`index.html` faylini brauzerda oching. Yaxshiroq natija uchun oddiy lokal server
bilan oching (masalan VS Code'da "Live Server" kengaytmasi), chunki forma va rasm
yo'llari ba'zi brauzerlarda `file://` orqali cheklanishi mumkin.

## Tuzilma
```
index.html              # asosiy sahifa
assets/css/main.css      # dizayn (ranglar, dark/light, komponentlar)
assets/js/main.js        # til (UZ/RU), tema, anketa yuborish logikasi
assets/js/config.js      # BOT TOKEN va CHAT ID shu yerda to'ldiriladi
assets/img/              # logotiplar va skrinshotlar
```

## Anketani Telegram botga ulash
`assets/js/config.js` faylini oching va quyidagilarni to'ldiring:

1. @BotFather'ga yozing → `/newbot` → botga nom bering → TOKEN oling.
2. Botni kerakli guruh/kanalga admin qilib qo'shing, yoki shaxsan botga `/start` yozing.
3. Chat ID'ni bilish uchun botga bir marta xabar yuboring, so'ng brauzerda oching:
   `https://api.telegram.org/bot<TOKEN>/getUpdates`
   Javobda `"chat":{"id": ...}` qismini toping.
4. `config.js` ichidagi `telegramBotToken` va `telegramChatId` qiymatlarini almashtiring.
5. `telegramBotUsername` ni ham to'ldiring (fallback tugma uchun, masalan `t.me/username`).

**Eslatma:** bu — tezkor, oddiy yechim. Token brauzer tomonida ochiq turadi.
Kelajakda xavfsizroq bo'lishi uchun anketani kichik backend (masalan n8n webhook
yoki Render.com'dagi FastAPI endpoint) orqali yuborish tavsiya etiladi — xohlasangiz,
buni ham qurib beraman.

## Ijtimoiy tarmoq havolalari
Xuddi shu `config.js` faylida `channels` ostida Telegram/Instagram/YouTube
havolalari bor — kerak bo'lsa shu yerda o'zgartirasiz.

## Deploy (Hostinger + Dokploy)
Bu statik sayt bo'lgani uchun eng oddiy yo'l: Dokploy'da "Static Site" turini
tanlab, shu papkani GitHub'ga push qilib ulash. Xohlasangiz, bosqichma-bosqich
yordam beraman.
