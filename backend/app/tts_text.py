"""Text normalisation for speech synthesis.

Small language models write sales replies the way a human reads them, not the
way a TTS engine needs them. ``$2,000``, ``11:00 AM`` and ``Thu, 26 Nov`` all
come out garbled or robotic if they are sent straight to a vocoder.

This module rewrites a reply into speakable English or Hindi. It is pure
Python, has no audio dependencies, and is unit tested in ``tests/test_voice.py``
so the voice service can stay a thin synthesiser.
"""

from __future__ import annotations

import re

from num2words import num2words

_MONTHS = {
    "jan": ("January", "जनवरी"),
    "feb": ("February", "फ़रवरी"),
    "mar": ("March", "मार्च"),
    "apr": ("April", "अप्रैल"),
    "may": ("May", "मई"),
    "jun": ("June", "जून"),
    "jul": ("July", "जुलाई"),
    "aug": ("August", "अगस्त"),
    "sep": ("September", "सितंबर"),
    "oct": ("October", "अक्टूबर"),
    "nov": ("November", "नवंबर"),
    "dec": ("December", "दिसंबर"),
}

_WEEKDAYS = {
    "mon": ("Monday", "सोमवार"),
    "tue": ("Tuesday", "मंगलवार"),
    "wed": ("Wednesday", "बुधवार"),
    "thu": ("Thursday", "गुरुवार"),
    "fri": ("Friday", "शुक्रवार"),
    "sat": ("Saturday", "शनिवार"),
    "sun": ("Sunday", "रविवार"),
}

_CURRENCIES = {
    "$": ("dollar", "dollars", "डॉलर", "डॉलर"),
    "₹": ("rupee", "rupees", "रुपया", "रुपये"),
    "€": ("euro", "euros", "यूरो", "यूरो"),
    "£": ("pound", "pounds", "पाउंड", "पाउंड"),
}

_HI_UNITS = [
    "शून्य", "एक", "दो", "तीन", "चार", "पाँच", "छह", "सात", "आठ", "नौ",
    "दस", "ग्यारह", "बारह", "तेरह", "चौदह", "पंद्रह", "सोलह", "सत्रह", "अठारह", "उन्नीस",
    "बीस", "इक्कीस", "बाईस", "तेईस", "चौबीस", "पच्चीस", "छब्बीस", "सत्ताईस", "अट्ठाईस", "उनतीस",
    "तीस", "इकतीस", "बत्तीस", "तैंतीस", "चौंतीस", "पैंतीस", "छत्तीस", "सैंतीस", "अड़तीस", "उनतालीस",
    "चालीस", "इकतालीस", "बयालीस", "तैंतालीस", "चवालीस", "पैंतालीस", "छियालीस", "सैंतालीस", "अड़तालीस", "उनचास",
    "पचास", "इक्यावन", "बावन", "तिरेपन", "चौवन", "पचपन", "छप्पन", "सत्तावन", "अट्ठावन", "उनसठ",
    "साठ", "इकसठ", "बासठ", "तिरेसठ", "चौंसठ", "पैंसठ", "छियासठ", "सड़सठ", "अड़सठ", "उनहत्तर",
    "सत्तर", "इकहत्तर", "बहत्तर", "तिहत्तर", "चौहत्तर", "पचहत्तर", "छिहत्तर", "सतहत्तर", "अठहत्तर", "उनासी",
    "अस्सी", "इक्यासी", "बयासी", "तिरासी", "चौरासी", "पचासी", "छियासी", "सत्तासी", "अट्ठासी", "नवासी",
    "नब्बे", "इक्यानवे", "बानवे", "तिरानवे", "चौरानवे", "पंचानवे", "छियानवे", "सत्तानवे", "अट्ठानवे", "निन्यानवे",
]

_EMOJI_RE = re.compile(
    "[" "\U0001f300-\U0001faff" "\U00002700-\U000027bf" "\U0001f1e6-\U0001f1ff"
    "\U00002600-\U000026ff" "\U0000fe0f" "\U00002b00-\U00002bff" "]",
    flags=re.UNICODE,
)


def _hi_int(value: int) -> str:
    """Hindi cardinal for 0..9,99,99,999 (enough for sales figures)."""
    if value < 0:
        return "माइनस " + _hi_int(-value)
    if value < 100:
        return _HI_UNITS[value]
    if value < 1000:
        hundreds, rest = divmod(value, 100)
        text = f"{_HI_UNITS[hundreds]} सौ"
        return f"{text} {_hi_int(rest)}" if rest else text
    if value < 100000:
        thousands, rest = divmod(value, 1000)
        text = f"{_hi_int(thousands)} हज़ार"
        return f"{text} {_hi_int(rest)}" if rest else text
    lakhs, rest = divmod(value, 100000)
    text = f"{_hi_int(lakhs)} लाख"
    return f"{text} {_hi_int(rest)}" if rest else text


def _is_hindi(language: str) -> bool:
    return (language or "").lower().startswith("hi")


def _number_words(raw: str, hindi: bool, ordinal: bool = False) -> str:
    digits = re.sub(r"[,\s]", "", raw)
    if not digits.isdigit() or len(digits) > 9:
        return raw.replace(",", "") if hindi else raw
    value = int(digits)
    if hindi:
        return _hi_int(value)
    return num2words(value, to="ordinal" if ordinal else "cardinal")


def _clean(text: str) -> str:
    text = _EMOJI_RE.sub(" ", text or "")
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"[*_`#>|]+", " ", text)
    text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)
    text = re.sub(r"https?://\S+", " ", text)
    text = text.replace("·", ",").replace("•", ",").replace("—", ", ")
    text = text.replace("&", " and ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s*\n+\s*", ". ", text)
    text = re.sub(r"\.\s*\.", ".", text)
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)
    return text.strip(" .")


def normalise_for_speech(text: str, language: str = "en-IN") -> str:
    """Rewrite a reply so a TTS voice reads it like a person would say it."""
    hindi = _is_hindi(language)
    text = _clean(text)
    if not text:
        return ""

    # 11:00 AM -> eleven AM / ग्यारह बजे
    def _time(match: re.Match[str]) -> str:
        hour = int(match.group(1))
        minute = int(match.group(2))
        suffix = (match.group(3) or "").lower()
        if hindi:
            hour_words = _hi_int(hour % 12 or 12)
            minute_words = "" if minute == 0 else f" {_hi_int(minute)}"
            return f"{hour_words}{minute_words} बजे"
        hour_words = num2words(hour % 12 or 12)
        meridiem = "AM" if suffix == "a" else "PM"
        if minute:
            return f"{hour_words} {num2words(minute)} {meridiem}"
        return f"{hour_words} {meridiem}"

    text = re.sub(r"\b(\d{1,2}):(\d{2})\s*([ap])\.?m\.?\b", _time, text, flags=re.IGNORECASE)

    # Thu, 26 Nov -> Thursday, the 26th of November / गुरुवार, 26 नवंबर
    def _date(match: re.Match[str]) -> str:
        day, month = match.group(1), match.group(2).lower()[:3]
        english_month, hindi_month = _MONTHS[month]
        if hindi:
            return f"{day} {hindi_month}"
        return f"the {num2words(int(day), to='ordinal')} of {english_month}"

    text = re.sub(
        r"\b(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b",
        _date,
        text,
        flags=re.IGNORECASE,
    )

    for short, (english, hindi_word) in _WEEKDAYS.items():
        text = re.sub(rf"\b{short}\b", hindi_word if hindi else english, text, flags=re.IGNORECASE)

    # $2,000 -> two thousand dollars / दो हज़ार डॉलर
    def _currency(match: re.Match[str]) -> str:
        symbol, amount = match.group(1), match.group(2)
        singular, plural, hi_singular, hi_plural = _CURRENCIES[symbol]
        digits = re.sub(r"[,\s]", "", amount)
        if not digits.isdigit():
            return match.group(0)
        value = int(digits)
        if hindi:
            return f"{_hi_int(value)} {hi_singular if value == 1 else hi_plural}"
        name = singular if value == 1 else plural
        return f"{num2words(value)} {name}"

    text = re.sub(r"([$₹€£])\s?([\d,]+(?:\.\d+)?)", _currency, text)

    # 40% -> forty percent / चालीस प्रतिशत
    def _percent(match: re.Match[str]) -> str:
        value = _number_words(match.group(1), hindi)
        return f"{value} प्रतिशत" if hindi else f"{value} percent"

    text = re.sub(r"(\d[\d,]*)\s?%", _percent, text)

    # Any remaining number: 1,000 -> one thousand
    def _plain(match: re.Match[str]) -> str:
        return _number_words(match.group(0), hindi)

    text = re.sub(r"\b\d[\d,]*(?:\.\d+)?\b", _plain, text)

    # Acronyms that a vocoder otherwise spells out letter by letter, badly.
    if hindi:
        text = re.sub(r"\bCRM\b", "सी आर एम", text)
        text = re.sub(r"\bAI\b", "ए आई", text)
    else:
        text = re.sub(r"\bCRM\b", "C R M", text)
        text = re.sub(r"\bAPI\b", "A P I", text)

    text = re.sub(r"\s+", " ", text).strip(" ,")
    if text and text[-1] not in ".!?।":
        text += "."
    return text


def split_sentences(text: str, max_chars: int = 190) -> list[str]:
    """Split a reply into speakable chunks so playback can start early."""
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    if not cleaned:
        return []

    parts = re.findall(r"[^.!?।]+[.!?।]+|[^.!?।]+$", cleaned)
    chunks: list[str] = []
    for part in parts:
        piece = part.strip()
        while len(piece) > max_chars:
            cut = max(piece.rfind(",", 0, max_chars), piece.rfind(" ", 0, max_chars))
            at = cut + 1 if cut > 40 else max_chars
            chunks.append(piece[:at].strip())
            piece = piece[at:].strip()
        if piece:
            chunks.append(piece)

    # A one-word chunk ("Sure.") sounds clipped on its own; merge it forward.
    merged: list[str] = []
    for chunk in chunks:
        if merged and len(merged[-1].split()) <= 3:
            merged[-1] = f"{merged[-1]} {chunk}".strip()
        else:
            merged.append(chunk)
    return merged or [cleaned]
