from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from config import ADMIN_ID

def get_main_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    """
    Doimiy pastki boshqaruv paneli tugmalari.
    Admin uchun maxsus '👑 Admin Panel' tugmasi qo'shiladi.
    """
    buttons = [
        [
            KeyboardButton(text="📊 Xotira holati"),
            KeyboardButton(text="🧹 Xotirani tozalash"),
        ]
    ]
    if user_id == ADMIN_ID:
        buttons.append([KeyboardButton(text="👑 Admin Panel")])

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="O'zbek tilida savol yozing..."
    )

def get_clear_confirm_inline() -> InlineKeyboardMarkup:
    """Xotirani tozalashni tasdiqlash uchun inline tugmalar"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha, tozalansin", callback_data="confirm_clear_memory"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_clear_memory"),
            ]
        ]
    )

def get_admin_panel_inline(live_notif: bool = True) -> InlineKeyboardMarkup:
    """Admin panel boshqaruv tugmalari"""
    notif_text = "🔔 Jonli kuzatuv: YOQILGAN" if live_notif else "🔕 Jonli kuzatuv: O'CHIRILGAN"
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Umumiy statistika", callback_data="admin_stats"),
                InlineKeyboardButton(text="📜 Oxirgi suhbatlar (10 ta)", callback_data="admin_logs_10"),
            ],
            [
                InlineKeyboardButton(text=notif_text, callback_data="admin_toggle_notif"),
            ],
            [
                InlineKeyboardButton(text="🔄 Yangilash", callback_data="admin_refresh"),
                InlineKeyboardButton(text="❌ Yopish", callback_data="admin_close"),
            ]
        ]
    )
