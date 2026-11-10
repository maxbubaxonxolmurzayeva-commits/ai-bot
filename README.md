# 1--bot (Telegram Bot)

Ushbu bot `/start` komandasi yuborilganda:
- Agar foydalanuvchida username bo'lsa: `Assalomu alekum, @username`
- Agar username bo'lmasa: `Assalomu alekum, hurmatli mijoz` deb javob beradi.

---

## 🚀 Serverga o'rnatish va 24/7 ishga tushirish

Botni serverda doimiy (uzluksiz) ishlatishning eng qulay usullari:

### 1-usul: Linux Serverda (Ubuntu / Debian VPS) Systemd orqali

1. **Serverga ulaning va kerakli paketlarni o'rnating:**
   ```bash
   sudo apt update && sudo apt install -y python3 python3-pip git
   ```

2. **Loyihani GitHub'dan serverga yuklab oling:**
   ```bash
   cd /var/www
   git clone https://github.com/maxbubaxonxolmurzayeva-commits/1--bot.git
   cd 1--bot
   ```

3. **Kutubxonalarni o'rnating:**
   ```bash
   pip3 install -r requirements.txt
   ```

4. **Botni 24/7 rejimda avtomatik ishlashi uchun xizmatni yoqing:**
   ```bash
   sudo cp bot.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable bot
   sudo systemctl start bot
   ```

5. **Holatini tekshirish:**
   ```bash
   sudo systemctl status bot
   ```

---

### 2-usul: Docker orqali ishga tushirish

Serveringizda Docker o'rnatilgan bo'lsa:

```bash
# Obrazni qurish
docker build -t telegram-bot .

# Konteynerni orqa fonda (restart bilan) ishga tushirish
docker run -d --restart always --name my-telegram-bot telegram-bot
```

---

### 3-usul: Bulutli bepul serverlarga ulash (Render.com / Railway.app)

1. [Render.com](https://render.com) yoki [Railway.app](https://railway.app) saytiga kiring va GitHub orqali kiring.
2. **"New Project"** -> **"Deploy from GitHub repo"** tugmasini bosing.
3. Repozitoriy sifatida `maxbubaxonxolmurzayeva-commits/1--bot` ni tanlang.
4. Turi sifatida **Background Worker** (yoki Docker) ni tanlang.
5. `Deploy` tugmasini bosing — bot avtomatik ishga tushadi!

---

## 💻 Kompyuterda (Lokal) ishga tushirish

1. Kutubxonalarni o'rnatish:
   ```bash
   pip install -r requirements.txt
   ```
2. Botni ishga tushirish:
   ```bash
   python main.py
   ```
   *(Windows foydalanuvchilari to'g'ridan-to'g'ri `Ishga_tushirish.bat` faylini ikki marta bosib ishga tushirishlari mumkin).*
