import os
import logging
import uuid
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart, Command
from aiogram.exceptions import TelegramBadRequest

from config import ADMIN_ID
from gemini_service import (
    ask_gemini_with_memory,
    transcribe_and_answer_audio,
    analyze_image_with_fallback,
    analyze_document_with_fallback
)
from memory_service import get_history_stats, clear_history
from database import (
    log_interaction,
    get_admin_stats,
    get_recent_chat_logs,
    get_setting,
    set_setting
)
from keyboards import (
    get_main_keyboard,
    get_clear_confirm_inline,
    get_admin_panel_inline
)
from formatters import markdown_to_telegram_html, strip_markdown
from file_processor import (
    TEMP_DIR,
    extract_text_from_docx,
    extract_text_from_excel,
    extract_text_from_txt
)

logger = logging.getLogger(__name__)
router = Router()

MAX_MESSAGE_LENGTH = 3900
MAX_FILE_SIZE = 2 * 1024 * 1024       # 2 MB (Hujjat va Rasmlar)
MAX_AUDIO_SIZE = 20 * 1024 * 1024     # 20 MB (Audio va Ovozlar)


async def notify_admin_live(bot: Bot, user: Message, query_type: str, query_text: str, reply_text: str, model_name: str):
    """
    Agar jonli kuzatuv yoqilgan bo'lsa va xabar adminga tegishli bo'lmasa,
    admin telegramiga darhol xabarnoma yuboradi.
    """
    try:
        if user.from_user.id == ADMIN_ID:
            return

        is_enabled = get_setting("live_notifications", "1") == "1"
        if not is_enabled:
            return

        u = user.from_user
        username = f"@{u.username}" if u.username else "mavjud emas"
        short_query = (query_text[:250] + "...") if len(query_text) > 250 else query_text
        short_reply = (reply_text[:350] + "...") if len(reply_text) > 350 else reply_text

        admin_alert = (
            "🔔 <b>Yangi muloqot kuzatildi!</b>\n\n"
            f"👤 <b>Foydalanuvchi:</b> {u.first_name} ({username})\n"
            f"🆔 <b>ID:</b> <code>{u.id}</code>\n"
            f"📂 <b>Format:</b> {query_type}\n\n"
            f"❓ <b>Savol:</b>\n<i>{short_query}</i>\n\n"
            f"🤖 <b>AI Javobi:</b>\n<i>{short_reply}</i>\n\n"
            f"⚡️ <b>Model:</b> <code>{model_name}</code>"
        )
        await bot.send_message(chat_id=ADMIN_ID, text=admin_alert, parse_mode="HTML")
    except Exception as e:
        logger.warning(f"Adminga jonli bildirishnoma yuborishda xatolik: {e}")


async def safe_reply_text(message: Message, raw_text: str):
    """Matnni Telegram HTML formatida chiroyli qilib yuborish"""
    html_text = markdown_to_telegram_html(raw_text)
    
    chunks = []
    current = ""
    for line in html_text.split("\n"):
        if len(current) + len(line) + 1 > MAX_MESSAGE_LENGTH:
            if current:
                chunks.append(current.strip())
                current = ""
            while len(line) > MAX_MESSAGE_LENGTH:
                chunks.append(line[:MAX_MESSAGE_LENGTH])
                line = line[MAX_MESSAGE_LENGTH:]
            current = line + "\n"
        else:
            current += line + "\n"
    if current.strip():
        chunks.append(current.strip())

    for chunk in chunks:
        try:
            await message.answer(chunk, parse_mode="HTML")
        except TelegramBadRequest:
            clean_chunk = strip_markdown(chunk)
            await message.answer(clean_chunk, parse_mode=None)


def format_stats_message(stats: dict) -> str:
    filled_blocks = int(stats["percentage"] // 10)
    empty_blocks = 10 - filled_blocks
    progress_bar = "🟩" * filled_blocks + "⬜" * empty_blocks

    return (
        "🧠 <b>Xotira boshqaruv paneli</b>\n\n"
        f"<b>Holat:</b> {stats['status_text']}\n"
        f"<b>Sig'im:</b> [{progress_bar}] {stats['percentage']}%\n\n"
        f"• <b>Saqlangan xabarlar:</b> {stats['count']} ta\n"
        f"• <b>Minimal kafolatlangan xotira:</b> {stats['min']} ta xabar\n"
        f"• <b>Maksimal xotira chegarasi:</b> {stats['max']} ta xabar\n\n"
        f"ℹ️ <i>{stats['description']}</i>"
    )


# ==================== BUYRUQLAR VA ASOSIY TUGMALAR ====================

@router.message(CommandStart())
async def handle_start(message: Message):
    u = message.from_user
    welcome_text = (
        f"Assalomu alaykum, <b>{u.first_name}</b>! Men universal Gemini AI yordamchisiman.\n\n"
        "✨ <b>4-bosqich yangiliklari:</b>\n"
        "• 🌐 <b>Internetdan qidirish:</b> Eng so'nggi yangiliklar, ma'lumotlar va voqealarni internetdan topib beraman.\n"
        "• 🎙 <b>O'zbekcha audio muloqot:</b> Ovozli xabarlarni o'zbek tilida transkripsiya qilaman va savolingizga javob beraman (TXT fayli bilan).\n"
        "• 🔄 <b>Avtomatik modellar zaxirasi:</b> Agar bitta model limitga yetsa, boshqa modelga bildirmasdan o'tib uzluksiz ishlayman.\n"
        "• 🧠 <b>Xotira:</b> Suhbat tarixini eslab qolaman.\n"
        "• 🖼 <b>Rasm va Hujjatlar:</b> PDF, Word, Excel, TXT (2 MB) va Audio (20 MB).\n\n"
        "Menga savolingizni yozing yoki fayl yuboring!"
    )
    await message.answer(
        welcome_text,
        parse_mode="HTML",
        reply_markup=get_main_keyboard(message.from_user.id)
    )


@router.message(F.text.in_({"📊 Xotira holati", "/memory"}))
async def handle_memory_stats(message: Message):
    stats = get_history_stats(message.from_user.id)
    text = format_stats_message(stats)
    await message.answer(text, parse_mode="HTML", reply_markup=get_main_keyboard(message.from_user.id))


@router.message(F.text.in_({"🧹 Xotirani tozalash", "/clear"}))
async def handle_clear_request(message: Message):
    stats = get_history_stats(message.from_user.id)
    if stats["count"] == 0:
        await message.answer("ℹ️ Xotirangiz hozirda bo'sh.", reply_markup=get_main_keyboard(message.from_user.id))
        return

    text = (
        f"⚠️ Xotirada <b>{stats['count']} ta xabar</b> saqlanmoqda.\n\n"
        "Haqiqatan ham barcha suhbat tarixini tozalab yubormoqchimisiz?"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_clear_confirm_inline())


@router.callback_query(F.data == "confirm_clear_memory")
async def handle_confirm_clear(call: CallbackQuery):
    deleted = clear_history(call.from_user.id)
    await call.message.edit_text(f"✅ Xotira muvaffaqiyatli tozalandi! ({deleted} ta xabar o'chirildi)")
    await call.answer("Xotira tozalandi!")


@router.callback_query(F.data == "cancel_clear_memory")
async def handle_cancel_clear(call: CallbackQuery):
    await call.message.edit_text("❌ Xotirani tozalash bekor qilindi.")
    await call.answer("Bekor qilindi")


# ==================== 👑 ADMIN PANEL ====================

@router.message(F.text.in_({"👑 Admin Panel", "/admin"}))
async def handle_admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Bu bo'lim faqat bot administratori uchun mo'ljallangan.")
        return

    stats = get_admin_stats()
    live_status = get_setting("live_notifications", "1") == "1"
    status_str = "🟢 Yoqilgan" if live_status else "🔴 O'chirilgan"

    text = (
        "👑 <b>Boshqaruv Paneli (Admin Dashboard)</b>\n\n"
        f"👥 <b>Jami foydalanuvchilar:</b> {stats['total_users']} nafar\n"
        f"💬 <b>Jami so'rovlar:</b> {stats['total_messages']} ta\n"
        f"📅 <b>Bugungi faol odamlar:</b> {stats['active_today']} nafar\n"
        f"✉️ <b>Bugungi xabarlar:</b> {stats['messages_today']} ta\n\n"
        f"🔔 <b>Jonli kuzatuv (Bildirishnoma):</b> {status_str}\n\n"
        "<i>Quyidagi tugmalar orqali boshqarishingiz mumkin:</i>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_admin_panel_inline(live_status))


@router.callback_query(F.data == "admin_stats")
async def handle_callback_admin_stats(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return await call.answer("Ruxsat yo'q!", show_alert=True)
    
    stats = get_admin_stats()
    text = (
        "📊 <b>Bot Statistikasi</b>\n\n"
        f"• Foydalanuvchilar soni: <b>{stats['total_users']}</b>\n"
        f"• Jami muloqotlar: <b>{stats['total_messages']}</b>\n"
        f"• Bugungi faol foydalanuvchilar: <b>{stats['active_today']}</b>\n"
        f"• Bugun berilgan savollar: <b>{stats['messages_today']}</b>"
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=call.message.reply_markup)
    await call.answer()


@router.callback_query(F.data == "admin_logs_10")
async def handle_callback_admin_logs(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return await call.answer("Ruxsat yo'q!", show_alert=True)

    logs = get_recent_chat_logs(limit=8)
    if not logs:
        await call.answer("Hozircha suhbatlar mavjud emas.", show_alert=True)
        return

    text = "📜 <b>Oxirgi suhbatlar:</b>\n\n"
    for idx, item in enumerate(logs, start=1):
        uname = f"@{item['username']}" if item['username'] else item['first_name']
        q_short = (item['user_query'][:70] + "...") if len(item['user_query']) > 70 else item['user_query']
        a_short = (item['ai_response'][:80] + "...") if len(item['ai_response']) > 80 else item['ai_response']
        
        text += (
            f"<b>{idx}. {uname}</b> [{item['message_type']}] | <code>{item['created_at']}</code>\n"
            f"❓ <i>{q_short}</i>\n"
            f"🤖 <i>{a_short}</i>\n"
            f"⚡️ <i>{item['model_used']}</i>\n\n"
        )

    await call.message.edit_text(text, parse_mode="HTML", reply_markup=call.message.reply_markup)
    await call.answer()


@router.callback_query(F.data == "admin_toggle_notif")
async def handle_callback_toggle_notif(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return await call.answer("Ruxsat yo'q!", show_alert=True)

    current = get_setting("live_notifications", "1") == "1"
    new_val = "0" if current else "1"
    set_setting("live_notifications", new_val)
    
    status_str = "yoqildi" if new_val == "1" else "o'chirildi"
    await call.answer(f"Jonli kuzatuv {status_str}!")
    await handle_admin_panel(call.message)


@router.callback_query(F.data == "admin_refresh")
async def handle_callback_admin_refresh(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return await call.answer()
    await handle_admin_panel(call.message)
    await call.answer("Yangilandi")


@router.callback_query(F.data == "admin_close")
async def handle_callback_admin_close(call: CallbackQuery):
    await call.message.delete()
    await call.answer()


# ==================== 1. OVOZ VA AUDIO HANDLER ====================
@router.message(F.voice | F.audio)
async def handle_audio_or_voice(message: Message, bot: Bot):
    audio_obj = message.voice or message.audio
    file_size = audio_obj.file_size or 0

    if file_size > MAX_AUDIO_SIZE:
        await message.answer(
            "⚠️ <b>Kechirasiz, audio fayl hajmi 20 MB dan oshmasligi kerak.</b>",
            parse_mode="HTML"
        )
        return

    is_voice = bool(message.voice)
    ext = ".ogg" if is_voice else os.path.splitext(message.audio.file_name or "audio.mp3")[1] or ".mp3"
    mime_type = "audio/ogg" if is_voice else (message.audio.mime_type or "audio/mp3")

    status_msg = await message.answer(
        "🎙 <i>Ovozli xabar qabul qilindi. O'zbek tilida transkripsiya qilinmoqda va javob tayyorlanmoqda...</i>",
        parse_mode="HTML"
    )
    await message.bot.send_chat_action(chat_id=message.chat.id, action="record_voice")

    unique_id = uuid.uuid4().hex
    temp_audio_path = os.path.join(TEMP_DIR, f"audio_{unique_id}{ext}")
    temp_txt_path = os.path.join(TEMP_DIR, f"transkripsiya_{unique_id}.txt")

    try:
        await bot.download(audio_obj, destination=temp_audio_path)
        
        # O'zbek tilida transkripsiya va savolga javob
        transcription_text, ai_reply, used_model = await transcribe_and_answer_audio(
            file_path=temp_audio_path,
            mime_type=mime_type
        )

        if not transcription_text:
            await status_msg.edit_text("Kechirasiz, audiodagi nutqni aniqlab bo'lmadi yoki audio bo'sh.")
            return

        # TXT faylga to'liq transkripsiyani yozish
        with open(temp_txt_path, "w", encoding="utf-8") as f:
            f.write(transcription_text)

        await status_msg.delete()

        # Foydalanuvchiga javob va transkripsiyani taqdim etish
        reply_caption = (
            f"🎙 <b>Sizning ovozli so'rovingiz:</b>\n<i>\"{transcription_text}\"</i>\n\n"
        )
        if ai_reply:
            reply_caption += f"🤖 <b>AI Javobi:</b>\n{ai_reply}"

        txt_file = FSInputFile(temp_txt_path, filename=f"transkripsiya_{unique_id[:8]}.txt")
        
        # Agar matn juda uzun bo'lsa, xabarga bo'lib yuboriladi
        if len(reply_caption) <= 1024:
            await message.answer_document(
                document=txt_file,
                caption=markdown_to_telegram_html(reply_caption),
                parse_mode="HTML"
            )
        else:
            await message.answer_document(
                document=txt_file,
                caption="📄 <b>To'liq transkripsiya ushbu TXT faylga yozildi.</b>",
                parse_mode="HTML"
            )
            await safe_reply_text(message, f"🤖 <b>AI Javobi:</b>\n{ai_reply}")

        # Bazaga va adminga yozish
        u = message.from_user
        log_interaction(
            user_id=u.id,
            username=u.username,
            first_name=u.first_name,
            last_name=u.last_name,
            message_type="Voice/Audio",
            user_query=transcription_text,
            ai_response=ai_reply or "Transkripsiya tayyorlandi",
            model_used=used_model
        )
        await notify_admin_live(
            bot=bot,
            user=message,
            query_type="🎙 Ovozli xabar",
            query_text=transcription_text,
            reply_text=ai_reply or "Transkripsiya tayyorlandi",
            model_name=used_model
        )

    except Exception as e:
        logger.error(f"Audio qayta ishlash xatosi: {e}", exc_info=True)
        await status_msg.edit_text("Audio tahlilida kutilmagan xatolik yuz berdi.")
    finally:
        for p in (temp_audio_path, temp_txt_path):
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass


# ==================== 2. RASM HANDLER ====================
@router.message(F.photo)
async def handle_photo(message: Message, bot: Bot):
    photo = message.photo[-1]
    if photo.file_size and photo.file_size > MAX_FILE_SIZE:
        await message.answer("⚠️ <b>Kechirasiz, rasm hajmi 2 MB dan oshmasligi kerak.</b>", parse_mode="HTML")
        return

    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    status_msg = await message.answer("🔍 <i>Rasm tahlil qilinmoqda...</i>", parse_mode="HTML")

    temp_path = os.path.join(TEMP_DIR, f"photo_{uuid.uuid4().hex}.jpg")
    try:
        await bot.download(photo, destination=temp_path)
        with open(temp_path, "rb") as f:
            image_bytes = f.read()

        caption = message.caption or "Rasm tahlili"
        reply_text, used_model = await analyze_image_with_fallback(message.from_user.id, image_bytes, caption=message.caption)
        
        await status_msg.delete()
        await safe_reply_text(message, reply_text)

        # Bazaga va adminga
        u = message.from_user
        log_interaction(
            user_id=u.id,
            username=u.username,
            first_name=u.first_name,
            last_name=u.last_name,
            message_type="Photo",
            user_query=caption,
            ai_response=reply_text,
            model_used=used_model
        )
        await notify_admin_live(bot, message, "🖼 Rasm", caption, reply_text, used_model)

    except Exception as e:
        logger.error(f"Rasm xatosi: {e}", exc_info=True)
        await status_msg.edit_text("Rasmni tahlil qilishda xatolik yuz berdi.")
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


# ==================== 3. HUJJATLAR HANDLER ====================
@router.message(F.document)
async def handle_document(message: Message, bot: Bot):
    doc = message.document
    file_size = doc.file_size or 0
    filename = doc.file_name or "document"
    ext = os.path.splitext(filename)[1].lower()

    if ext in {".mp3", ".ogg", ".wav", ".m4a", ".aac", ".flac", ".opus"}:
        if file_size > MAX_AUDIO_SIZE:
            await message.answer("⚠️ Audio hajmi 20 MB dan oshmasligi kerak.")
            return
        message.audio = doc
        return await handle_audio_or_voice(message, bot)

    if file_size > MAX_FILE_SIZE:
        await message.answer(f"⚠️ <b>'{filename}' fayli hajmi 2 MB dan katta.</b> Iltimos, kichikroq fayl yuboring.", parse_mode="HTML")
        return

    supported_exts = {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".txt", ".csv"}
    if ext not in supported_exts:
        await message.answer("⚠️ Faqat PDF, Word, Excel yoki TXT fayllar qabul qilinadi.", parse_mode="HTML")
        return

    await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_document")
    status_msg = await message.answer(f"📄 <i>'{filename}' tahlil qilinmoqda...</i>", parse_mode="HTML")

    temp_path = os.path.join(TEMP_DIR, f"doc_{uuid.uuid4().hex}{ext}")
    try:
        await bot.download(doc, destination=temp_path)
        extracted_text = None
        mime_type = doc.mime_type or "application/octet-stream"

        if ext in {".docx", ".doc"}:
            extracted_text = extract_text_from_docx(temp_path)
        elif ext in {".xlsx", ".xls"}:
            extracted_text = extract_text_from_excel(temp_path)
        elif ext in {".txt", ".csv"}:
            extracted_text = extract_text_from_txt(temp_path)
        elif ext == ".pdf":
            mime_type = "application/pdf"

        caption = message.caption or f"{filename} tahlili"
        reply_text, used_model = await analyze_document_with_fallback(
            user_id=message.from_user.id,
            file_path=temp_path,
            filename=filename,
            mime_type=mime_type,
            caption=message.caption,
            extracted_text=extracted_text
        )

        await status_msg.delete()
        await safe_reply_text(message, reply_text)

        u = message.from_user
        log_interaction(
            user_id=u.id,
            username=u.username,
            first_name=u.first_name,
            last_name=u.last_name,
            message_type=f"Doc ({ext})",
            user_query=caption,
            ai_response=reply_text,
            model_used=used_model
        )
        await notify_admin_live(bot, message, f"📄 Hujjat ({ext})", caption, reply_text, used_model)

    except Exception as e:
        logger.error(f"Hujjat tahlili xatosi: {e}", exc_info=True)
        await status_msg.edit_text("Hujjatni tahlil qilishda xatolik yuz berdi.")
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


# ==================== 4. MATN HANDLER ====================
@router.message(F.text)
async def handle_text(message: Message, bot: Bot):
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    reply_text, used_model = await ask_gemini_with_memory(message.from_user.id, message.text)
    await safe_reply_text(message, reply_text)

    # Bazaga va adminga
    u = message.from_user
    log_interaction(
        user_id=u.id,
        username=u.username,
        first_name=u.first_name,
        last_name=u.last_name,
        message_type="Text",
        user_query=message.text,
        ai_response=reply_text,
        model_used=used_model
    )
    await notify_admin_live(bot, message, "💬 Matn", message.text, reply_text, used_model)


# ==================== 5. BOSHQA FORMATLAR ====================
@router.message(~F.text)
async def handle_other_media(message: Message):
    warning_text = (
        "Kechirasiz, ushbu format qo'llab-quvvatlanmaydi.\n\n"
        "Siz quyidagilarni yuborishingiz mumkin:\n"
        "• <b>Matn:</b> Savollaringiz (internetdan qidirish bilan)\n"
        "• <b>Ovozli xabar / Audio:</b> 20 MB gacha transkripsiya va javob uchun\n"
        "• <b>Rasm:</b> 2 MB gacha tahlil uchun\n"
        "• <b>Hujjatlar:</b> 2 MB gacha PDF, Word, Excel, TXT"
    )
    await message.answer(warning_text, parse_mode="HTML", reply_markup=get_main_keyboard(message.from_user.id))
