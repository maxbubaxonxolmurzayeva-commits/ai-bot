# Gemini AI Telegram Bot (4-bosqich: Google Search, Model Fallback, Audio Q&A, Admin Panel)

Telegram messenjeri uchun Google Gemini sun'iy intellekti bilan integratsiya qilingan kuchli va aqlli universal botning **4-bosqich** versiyasi.

---

## 📌 4-bosqich yangiliklari va imkoniyatlari:

1. **🎙 O'zbekcha audio transkripsiyasi va savolga javob:**
   - Ovozli xabarlar o'zbek tiliga qat'iy moslashtirildi.
   - Audiodagi nutq to'liq `.txt` fayl sifatida foydalanuvchiga taqdim etiladi.
   - **Eng muhimi:** Agar audioda savol yoki murojaat bo'lsa, Gemini ushbu savolga ham o'zbek tilida to'laqonli AI javobini beradi!

2. **🌐 Internetdan qidirish (Google Search Grounding):**
   - Gemini internetga ulandi. Eng so'nggi yangiliklar, ob-havo, valyuta kurslari, dolzarb voqealar haqida internetdan izlab javob beradi.

3. **🔄 Avtomatik modellar zaxirasi (Model Fallback Pool):**
   - Agar biror model kvota limiti (429 RESOURCE_EXHAUSTED) yoki yuklama (503) ga uchrasa, bot zaxiradagi boshqa modellarga (`gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`, `gemini-3.5-flash`, `gemini-3.6-flash`, `gemini-3.8-flash`...) avtomatik va bildirmasdan o'tib uzluksiz javob qaytaradi.
   - Foydalanuvchiga hech qachon xatolik ko'rsatilmaydi!

4. **👑 Admin Panel va Jonli monitoring:**
   - **Admin ID:** `1948392026`
   - **`/admin`** yoki **"👑 Admin Panel"** menyusi orqali:
     - 📊 Umumiy foydalanuvchilar va so'rovlar statistikasi.
     - 📜 Jonli suhbatlar: Boshqa insonlar qanaqa savollar berayotgani va AI nima javob berganini ko'rish.
     - 🔔 Jonli kuzatuv (Live Alert): Boshqa odamlar botga yozganda admin telegramiga real-vaqtda bildirishnoma boradi.

5. **2-3-bosqich imkoniyatlari saqlanadi:**
   - 20-50 ta xabarlik SQLite xotira.
   - Chiroyli Telegram HTML formatlash.
   - Rasm (2 MB gacha) va Hujjatlar: PDF, Word, Excel, TXT (2 MB gacha).

---

## 📁 Loyiha tuzilmasi

```text
AI chat bot/
├── .env                # BOT_TOKEN, GEMINI_API_KEY, ADMIN_ID
├── config.py           # Sozlamalar va tekshiruvlar
├── database.py         # Foydalanuvchilar, chat loglari va admin statistikasi
├── memory_service.py   # SQLite xotira mexanizmi
├── file_processor.py   # Word (docx), Excel (xlsx), TXT fayllarni o'qish
├── formatters.py       # Telegram HTML formati
├── gemini_service.py   # Gemini AI (Search, Fallback Pool, Audio Q&A)
├── keyboards.py        # Admin va foydalanuvchi klaviaturalari
├── handlers.py         # Barcha handlerlar va admin boshqaruvi
├── main.py             # Botni ishga tushirish nuqtasi
├── memory.db           # SQLite bazasi
└── requirements.txt    # Kerakli paketlar
```

---

## 🚀 Ishga tushirish

```bash
python main.py
```
