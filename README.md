# Telegram Bot

Ushbu bot `/start` komandasi yuborilganda:
- Agar foydalanuvchida username bo'lsa: `Assalomu alekum, @username`
- Agar username bo'lmasa: `Assalomu alekum, hurmatli mijoz` deb javob beradi.

## Ishga tushirish qadamlari:

1. **Python o'rnatish**:
   - [python.org](https://www.python.org/downloads/) saytidan Python-ni yuklab olib o'rnating.
   - O'rnatish paytida **"Add python.exe to PATH"** katakchasiga belgi qo'yishni unutmang!

2. **Telegramda bot yaratish va token olish**:
   - Telegramda [@BotFather](https://t.me/BotFather) botiga kiring.
   - `/newbot` buyrug'ini yuboring.
   - Bot nomini va unikal username'ini kiriting.
   - BotFather sizga **HTTP API token** beradi (masalan: `1234567890:ABCdef...`).

3. **Kodni sozlash**:
   - `main.py` faylini oching va `BOT_TOKENINI_SHU_YERGA_YOZING` o'rniga BotFather bergan tokenni qo'ying.

4. **Kutubxonani o'rnatish va botni yurgazish**:
   Terminal yoki CMD (PowerShell) ochib, ushbu buyruqlarni bajaring:
   ```bash
   pip install -r requirements.txt
   python main.py
   ```
