import html
import re

def markdown_to_telegram_html(text: str) -> str:
    """
    Gemini qaytargan Markdown matnni Telegram HTML formatiga o'tkazadi
    va yulduzchalar (*, **) o'rniga chiroyli <b>, <i> teglarini qo'yadi.
    """
    if not text:
        return ""

    # Kod bloklarini vaqtinchalik saqlab turish
    code_blocks = []
    def save_code_block(match):
        code_blocks.append(match.group(0))
        return f"__CODE_BLOCK_{len(code_blocks) - 1}__"

    # Ko'p qatorli kod bloklari: ```lang ... ```
    text = re.sub(r"```[\w]*\n?[\s\S]*?```", save_code_block, text)

    # Inline kod bloklari: `...`
    inline_codes = []
    def save_inline_code(match):
        inline_codes.append(match.group(0))
        return f"__INLINE_CODE_{len(inline_codes) - 1}__"

    text = re.sub(r"`[^`\n]+`", save_inline_code, text)

    # HTML maxsus belgilarini escape qilish (&, <, >)
    text = html.escape(text)

    # Sarlavhalarni qalin matnga aylantirish: ### Sarlavha -> <b>Sarlavha</b>
    text = re.sub(r"^(?:#{1,6})\s+(.+)$", r"<b>\1</b>", text, flags=re.MULTILINE)

    # Ro'yxat belgilarini chiroyli nuqtaga aylantirish: * yoki - band -> • band
    text = re.sub(r"^[\*\-]\s+(.+)$", r"• \1", text, flags=re.MULTILINE)

    # Qalin va qiyiq: ***matn*** -> <b><i>matn</i></b>
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"<b><i>\1</i></b>", text)

    # Qalin matn: **matn** -> <b>matn</b>
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)

    # Qiyiq matn: *matn* -> <i>matn</i>
    text = re.sub(r"(?<!\*)\*([^\*\n]+?)\*(?!\*)", r"<i>\1</i>", text)

    # Tag chizilgan yoki kursiv matn: _matn_ -> <i>matn</i>
    text = re.sub(r"(?<!_)_([^_\n]+?)_(?!_)", r"<i>\1</i>", text)

    # Inline kodlarni qaytarish
    for i, code in enumerate(inline_codes):
        clean_code = code.strip("`")
        escaped = html.escape(clean_code)
        text = text.replace(f"__INLINE_CODE_{i}__", f"<code>{escaped}</code>")

    # Kod bloklarini qaytarish
    for i, block in enumerate(code_blocks):
        # ```python\ncode\n```
        lines = block.split("\n", 1)
        lang = lines[0].replace("```", "").strip()
        body = lines[1][:-3] if len(lines) > 1 and lines[1].endswith("```") else block.strip("`")
        escaped_body = html.escape(body.strip("\n"))
        text = text.replace(f"__CODE_BLOCK_{i}__", f"<pre><code>{escaped_body}</code></pre>")

    return text.strip()


def strip_markdown(text: str) -> str:
    """
    Agar HTML parse_mode xatolik bersa, barcha yulduzcha va belgilarni
    tozalab, oddiy chiroyli matn holatiga keltiradi (fallback).
    """
    if not text:
        return ""
    # Sarlavha panjaralarini olib tashlash
    text = re.sub(r"^(?:#{1,6})\s+", "", text, flags=re.MULTILINE)
    # Ro'yxat yulduzchalarini chiroyli nuqta qilish
    text = re.sub(r"^[\*\-]\s+", "• ", text, flags=re.MULTILINE)
    # Ko'p yulduzchalarni tozalash (***so'z*** -> so'z, **so'z** -> so'z, *so'z* -> so'z)
    text = re.sub(r"\*{1,3}([^\*]+?)\*{1,3}", r"\1", text)
    # Tag chiziqlarini tozalash
    text = re.sub(r"_{1,2}([^_]+?)_{1,2}", r"\1", text)
    return text.strip()
