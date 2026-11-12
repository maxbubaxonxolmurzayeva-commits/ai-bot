import sqlite3
import os
from typing import List, Dict, Any
from google.genai import types

DB_PATH = os.path.join(os.path.dirname(__file__), "memory.db")

MAX_MESSAGES = 50  # Eng ko'pi bilan 50 ta xabar saqlanadi
MIN_MESSAGES = 20  # Xotira uchun kafolatlangan minimal sig'im

def init_db():
    """Ma'lumotlar bazasini va jadvalini yaratish"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_history 
            ON conversation_history(user_id, id)
        """)
        conn.commit()

# Modul yuklanganda bazani ishga tushirish
init_db()

def add_message(user_id: int, role: str, content: str):
    """
    Yangi xabarni (user yoki model) xotiraga qo'shish.
    Agar xabarlar soni MAX_MESSAGES (50) dan oshsa, eng eskilari o'chiriladi.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO conversation_history (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content)
        )
        
        # 50 tadan oshgan eski xabarlarni o'chirish (sliding window)
        cursor.execute("""
            DELETE FROM conversation_history
            WHERE user_id = ? AND id NOT IN (
                SELECT id FROM conversation_history
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
            )
        """, (user_id, user_id, MAX_MESSAGES))
        conn.commit()

def clear_history(user_id: int) -> int:
    """Foydalanuvchining barcha suhbat xotirasini tozalaydi."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM conversation_history WHERE user_id = ?", (user_id,))
        deleted_count = cursor.rowcount
        conn.commit()
        return deleted_count

def get_history_stats(user_id: int) -> Dict[str, Any]:
    """
    Foydalanuvchining xotira holati statistikasi.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM conversation_history WHERE user_id = ?",
            (user_id,)
        )
        count = cursor.fetchone()[0]

    percentage = round((count / MAX_MESSAGES) * 100, 1)

    if count == 0:
        status_text = "🟢 Xotira bo'sh (0%)"
        description = "Hozircha hech qanday suhbat xotirada saqlanmagan."
    elif count < MIN_MESSAGES:
        status_text = f"🟢 Xotira me'yorda ({percentage}%)"
        description = f"Xotirada {count} ta xabar mavjud (kamida {MIN_MESSAGES} ta xabar doimiy kafolatlanadi)."
    elif count < MAX_MESSAGES:
        status_text = f"🟡 Xotira faol to'lmoqda ({percentage}%)"
        description = f"Xotirada {count} ta xabar mavjud. Maksimal sig'im {MAX_MESSAGES} tagacha."
    else:
        status_text = f"🔴 Xotira to'liq ({percentage}%)"
        description = (
            f"Xotira maksimal sig'imga ({MAX_MESSAGES} ta) yetgan. "
            "Yangi xabarlar kelganda eng eski xabarlar avtomatik ravishda yangilanadi."
        )

    return {
        "count": count,
        "max": MAX_MESSAGES,
        "min": MIN_MESSAGES,
        "percentage": percentage,
        "status_text": status_text,
        "description": description
    }

def get_gemini_contents_with_history(user_id: int, current_user_message: str) -> List[types.Content]:
    """
    Foydalanuvchining avvalgi xabarlarini olib, Gemini API formati
    (List[types.Content]) ga o'tkazadi va yangi xabarni oxiriga qo'shadi.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT role, content FROM conversation_history
            WHERE user_id = ?
            ORDER BY id ASC
        """, (user_id,))
        rows = cursor.fetchall()

    contents: List[types.Content] = []

    # Tarixdan ketma-ket qo'shish
    for role, text in rows:
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=text)]
            )
        )

    # Gemini qoidasi: suhbat tarixi birinchi navbatda 'user' roli bilan boshlanishi kerak
    while contents and contents[0].role != "user":
        contents.pop(0)

    # Yangi xabarni qo'shish
    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=current_user_message)]
        )
    )

    return contents
