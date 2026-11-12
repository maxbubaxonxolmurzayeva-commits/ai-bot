import sqlite3
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "memory.db")

def init_all_tables():
    """Barcha jadvallarni yaratish va indekslarni sozlash"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # 1. Suhbat xotirasi (Conversation memory)
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

        # 2. Foydalanuvchilar jadvali (Users)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                total_messages INTEGER DEFAULT 1,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 3. Admin uchun to'liq suhbatlar jurnali (Audit / Chat Logs)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                first_name TEXT,
                message_type TEXT NOT NULL,
                user_query TEXT,
                ai_response TEXT,
                model_used TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chat_logs_time 
            ON chat_logs(id DESC)
        """)
        
        # 4. Admin sozlamalari (jonli bildirishnoma yoqilganmi-yo'qmi)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        # Standart bo'yicha jonli bildirishnoma yoqilgan (1)
        cursor.execute("""
            INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('live_notifications', '1')
        """)
        
        conn.commit()

init_all_tables()


def log_interaction(
    user_id: int,
    username: Optional[str],
    first_name: Optional[str],
    last_name: Optional[str],
    message_type: str,
    user_query: str,
    ai_response: str,
    model_used: str = "gemini"
):
    """Foydalanuvchi va AI o'rtasidagi so'rov-javobni bazaga saqlash va profilni yangilash"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Foydalanuvchini yangilash yoki qo'shish
        cursor.execute("""
            INSERT INTO bot_users (user_id, username, first_name, last_name, total_messages, last_seen)
            VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                last_name = excluded.last_name,
                total_messages = total_messages + 1,
                last_seen = CURRENT_TIMESTAMP
        """, (user_id, username, first_name, last_name))
        
        # Muloqot logini saqlash
        cursor.execute("""
            INSERT INTO chat_logs (user_id, username, first_name, message_type, user_query, ai_response, model_used)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, username, first_name, message_type, user_query, ai_response, model_used))
        
        conn.commit()


def get_admin_stats() -> Dict[str, Any]:
    """Admin uchun to'liq statistika"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM bot_users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM chat_logs")
        total_messages = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) FROM chat_logs 
            WHERE date(created_at) = date('now')
        """)
        active_today = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM chat_logs 
            WHERE date(created_at) = date('now')
        """)
        messages_today = cursor.fetchone()[0]
        
    return {
        "total_users": total_users,
        "total_messages": total_messages,
        "active_today": active_today,
        "messages_today": messages_today,
    }


def get_recent_chat_logs(limit: int = 10) -> List[Dict[str, Any]]:
    """Oxirgi so'rov-javoblarni olish"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, username, first_name, message_type, user_query, ai_response, model_used, created_at
            FROM chat_logs
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()

    logs = []
    for r in rows:
        logs.append({
            "id": r[0],
            "user_id": r[1],
            "username": r[2],
            "first_name": r[3],
            "message_type": r[4],
            "user_query": r[5],
            "ai_response": r[6],
            "model_used": r[7],
            "created_at": r[8],
        })
    return logs


def get_all_user_ids() -> List[int]:
    """Barcha foydalanuvchilar ID ro'yxati (xabarnoma tarqatish uchun)"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM bot_users")
        return [row[0] for row in cursor.fetchall()]


def get_setting(key: str, default: str = "") -> str:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM bot_settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else default


def set_setting(key: str, value: str):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO bot_settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (key, value))
        conn.commit()
