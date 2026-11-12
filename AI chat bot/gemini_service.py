import logging
import os
from typing import List, Optional, Tuple
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, GEMINI_MODEL
from memory_service import (
    get_gemini_contents_with_history,
    add_message
)

logger = logging.getLogger(__name__)

# Modellarning ustuvorlik tartibi (biri limitga uchrasa, darhol keyingisiga o'tadi)
FALLBACK_MODELS = [
    GEMINI_MODEL,              # Standart model (gemini-3.5-flash-lite)
    "gemini-3.1-flash-lite",   # 1-zaxira
    "gemini-3.5-flash",        # 2-zaxira
    "gemini-3.6-flash",        # 3-zaxira
    "gemini-3.8-flash",        # 4-zaxira
    "gemini-3.7-flash",        # 5-zaxira
]
# Dublikatlarni olib tashlash
FALLBACK_MODELS = list(dict.fromkeys([m for m in FALLBACK_MODELS if m]))

SYSTEM_INSTRUCTION = """Siz har tomonlama intellektual va foydali yordamchi sun'iy intellektsiz.

QAT'IY QOIDALAR:
1. Siz FAQAT va FAQAT O'ZBEK TILIDA javob berasiz.
2. Agar foydalanuvchi xabari o'zbek tilida bo'lmasa (rus, ingliz va boshqa tillarda bo'lsa), savolga javob bermang va quyidagicha qisqa javob qaytaring:
"Kechirasiz, men ushbu tilda gaplasha olmayman. Iltimos, menga faqat o'zbek tilida yozing."
3. Agar foydalanuvchi joriy yangiliklar, ob-havo, valyuta kurslari, yangi voqealar yoki ma'lumotlar haqida so'rasa, internetdan izlab eng so'nggi va aniq ma'lumotlarni o'zbek tilida taqdim eting.
4. Suhbat tarixini (xotirani) eslab qoling va shunga mos holda davom ettiring.
5. Javoblarda xunuk formatlash belgilarini (keraksiz yulduzchalarni) ishlatmang. Chiroyli, tartibli va adabiy o'zbek tilida yozing.
"""

_client = None

def get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


async def generate_with_fallback(
    contents: any,
    system_instruction: str = SYSTEM_INSTRUCTION,
    enable_search: bool = True,
    temperature: float = 0.7
) -> Tuple[Optional[str], str]:
    """
    Barcha zaxira modellarni navbatma-navbat sinab ko'radi.
    Agar bittasi limitga uchrasa (429, 503 va h.k.), keyingisiga avtomatik o'tadi.
    Qidiruv (Google Search) xato bersa, oddiy rejimda qayta urinadi.
    Qaytaradi: (javob_matni, ishlatilgan_model_nomi)
    """
    client = get_client()
    last_error = None

    for model_name in FALLBACK_MODELS:
        # 1-urinish: Google Search bilan (agar yoqilgan bo'lsa)
        if enable_search:
            try:
                config = types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=temperature,
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                )
                response = await client.aio.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config
                )
                if response.text and response.text.strip():
                    return response.text.strip(), f"{model_name} (Search)"
            except Exception as e:
                logger.warning(f"Model {model_name} (Search bilan) xato berdi: {e}. Qidiruvsiz urinib ko'rilmoqda...")

        # 2-urinish: Qidiruvsiz oddiy rejimda
        try:
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=temperature
            )
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=contents,
                config=config
            )
            if response.text and response.text.strip():
                return response.text.strip(), model_name
        except Exception as e:
            last_error = e
            logger.warning(f"Model {model_name} limitga yoki xatoga uchradi: {e}. Keyingi modelga o'tilmoqda...")
            continue

    logger.error(f"Barcha modellar sinab ko'rildi, oxirgi xatolik: {last_error}")
    return None, "none"


async def ask_gemini_with_memory(user_id: int, user_prompt: str) -> Tuple[str, str]:
    """
    Foydalanuvchi so'rovini xotira, internet qidiruvi va modellar zaxirasi bilan bajaradi.
    Qaytaradi: (javob_matni, ishlatilgan_model)
    """
    contents = get_gemini_contents_with_history(user_id, user_prompt)
    reply_text, used_model = await generate_with_fallback(
        contents=contents,
        enable_search=True,
        temperature=0.7
    )
    
    if reply_text:
        add_message(user_id, "user", user_prompt)
        add_message(user_id, "model", reply_text)
        return reply_text, used_model

    # Agar barcha modellar ishlamay qolsa ham foydalanuvchiga chiroyli muloyim javob:
    fallback_msg = (
        "Hozirda tizimda vaqtinchalik yuqori yuklama mavjud. "
        "Iltimos, bir ozdan so'ng savolingizni qayta yuboring."
    )
    return fallback_msg, "fallback"


async def transcribe_and_answer_audio(file_path: str, mime_type: str = "audio/ogg") -> Tuple[Optional[str], Optional[str], str]:
    """
    Ovozli xabar/audiodan nutqni O'ZBEK TILIDA aniq transkripsiya qiladi
    va shu savolga Gemini orqali o'zbek tilida to'liq javob tayyorlaydi!
    Qaytaradi: (transkripsiya_matni, ai_javobi, ishlatilgan_model)
    """
    client = get_client()
    uploaded_file = None
    try:
        # Faylni Gemini File API ga yuklash
        uploaded_file = await client.aio.files.upload(
            file=file_path,
            config=types.UploadFileConfig(mime_type=mime_type)
        )
        
        # O'zbek tiliga moslashtirilgan qat'iy transkripsiya ko'rsatmasi
        transcribe_prompt = (
            "DIQQAT: Ushbu audiodagi gapiruvchi o'zbek tilida so'zlamoqda. "
            "Audiodagi nutqni diqqat bilan eshitib, to'g'ri o'zbek adabiy tilida (lotin alifbosida) "
            "so'zma-so'z to'liq transkripsiya qiling. Kirish yoki xulosalarsiz, faqat nutq matnini yozing."
        )
        
        transcription_text = None
        used_model = "unknown"
        
        for m_name in FALLBACK_MODELS:
            try:
                resp = await client.aio.models.generate_content(
                    model=m_name,
                    contents=[uploaded_file, transcribe_prompt],
                    config=types.GenerateContentConfig(temperature=0.1)
                )
                if resp.text and resp.text.strip():
                    transcription_text = resp.text.strip()
                    used_model = m_name
                    break
            except Exception as e:
                logger.warning(f"Audio transkripsiyada {m_name} xatosi: {e}")
                continue

        if not transcription_text:
            return None, None, "none"

        # Endi transkripsiya qilingan savolga to'liq javob shakllantirish
        answer_prompt = (
            f"Foydalanuvchi ovozli xabar orqali quyidagi savol/murojaatni yubordi:\n"
            f"\"{transcription_text}\"\n\n"
            f"Ushbu so'rovga o'zbek tilida to'liq, aniq, muloyim va foydali tarzda javob bering."
        )
        ai_reply, ans_model = await generate_with_fallback(
            contents=answer_prompt,
            enable_search=True,
            temperature=0.6
        )

        return transcription_text, ai_reply, used_model

    except Exception as e:
        logger.error(f"Audio qayta ishlash xatosi: {e}", exc_info=True)
        return None, None, "error"
    finally:
        if uploaded_file and hasattr(uploaded_file, "name"):
            try:
                await client.aio.files.delete(name=uploaded_file.name)
            except Exception:
                pass


async def analyze_image_with_fallback(user_id: int, image_bytes: bytes, caption: Optional[str] = None) -> Tuple[str, str]:
    """Rasmni zaxira modellar bilan tahlil qilish."""
    image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
    prompt_text = caption.strip() if caption and caption.strip() else (
        "Ushbu rasmni diqqat bilan tahlil qiling. Unda nimalar aks etganini, "
        "agar matn, jadval yoki diagramma bo'lsa ularni o'qib, "
        "o'zbek tilida to'liq va batafsil tushuntirib bering."
    )
    
    reply_text, used_model = await generate_with_fallback(
        contents=[image_part, prompt_text],
        enable_search=False,
        temperature=0.4
    )
    if reply_text:
        add_message(user_id, "user", f"[Rasm]: {prompt_text}")
        add_message(user_id, "model", reply_text)
        return reply_text, used_model
    return "Kechirasiz, rasmni tahlil qilish imkoni bo'lmadi.", "fallback"


async def analyze_document_with_fallback(
    user_id: int,
    file_path: str,
    filename: str,
    mime_type: str,
    caption: Optional[str] = None,
    extracted_text: Optional[str] = None
) -> Tuple[str, str]:
    """Hujjatlarni zaxira modellar bilan tahlil qilish."""
    client = get_client()
    uploaded_file = None
    prompt_text = caption.strip() if caption and caption.strip() else (
        f"Ushbu '{filename}' nomli hujjatni batafsil tahlil qiling. "
        "Uning asosiy mazmuni, muhim ma'lumotlari va xulosalarini "
        "o'zbek tilida tartibli va tushunarli qilib yoritib bering."
    )
    
    try:
        if extracted_text:
            contents = [
                f"Hujjat nomi: {filename}\n\nHujjat mazmuni:\n{extracted_text[:40000]}",
                prompt_text
            ]
        else:
            uploaded_file = await client.aio.files.upload(
                file=file_path,
                config=types.UploadFileConfig(mime_type=mime_type)
            )
            contents = [uploaded_file, prompt_text]

        reply_text, used_model = await generate_with_fallback(
            contents=contents,
            enable_search=False,
            temperature=0.4
        )
        if reply_text:
            add_message(user_id, "user", f"[Hujjat: {filename}]: {prompt_text}")
            add_message(user_id, "model", reply_text)
            return reply_text, used_model
        return "Kechirasiz, hujjatni tahlil qilish imkoni bo'lmadi.", "fallback"
    finally:
        if uploaded_file and hasattr(uploaded_file, "name"):
            try:
                await client.aio.files.delete(name=uploaded_file.name)
            except Exception:
                pass
