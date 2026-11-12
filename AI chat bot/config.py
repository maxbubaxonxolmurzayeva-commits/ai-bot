import os
import sys
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()

try:
    ADMIN_ID = int(os.getenv("ADMIN_ID", "1948392026").strip())
except ValueError:
    ADMIN_ID = 1948392026

def validate_config():
    missing = []
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")
    
    if missing:
        print("\n" + "=" * 50)
        print("XATOLIK: Quyidagi kalitlar .env faylida topilmadi:")
        for item in missing:
            print(f" - {item}")
        print("\nIltimos, .env faylini oching va qiymatlarni kiriting.")
        print("=" * 50 + "\n")
        sys.exit(1)
