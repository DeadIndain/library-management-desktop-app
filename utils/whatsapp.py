"""
WhatsApp messaging utility using pywhatkit.
Opens WhatsApp Web and sends messages automatically.
"""
import threading
from typing import Optional
import webbrowser
import urllib.parse


def _clean_phone(phone: str) -> str:
    """Normalize phone to E.164-ish string: +91XXXXXXXXXX"""
    cleaned = "".join(c for c in phone if c.isdigit() or c == "+")
    if not cleaned.startswith("+"):
        cleaned = "+91" + cleaned
    return cleaned


def get_whatsapp_chat_link(phone: str) -> str:
    """Return a wa.me deep link for the given phone number."""
    return f"https://wa.me/{_clean_phone(phone).lstrip('+')}"


def get_whatsapp_chat_link_with_message(phone: str, message: str) -> str:
    """Return a wa.me deep link pre-filled with a message."""
    encoded = urllib.parse.quote(message)
    return f"https://wa.me/{_clean_phone(phone).lstrip('+')}?text={encoded}"


def open_whatsapp_chat(phone: str, message: str = ""):
    """Open WhatsApp chat in browser (wa.me link)."""
    if message:
        webbrowser.open(get_whatsapp_chat_link_with_message(phone, message))
    else:
        webbrowser.open(get_whatsapp_chat_link(phone))


def _send_whatsapp_background(phone: str, message: str, tab_close: bool = True,
                               close_time: int = 5, wait_time: int = 20):
    try:
        import pywhatkit as kit
        cleaned = _clean_phone(phone)
        kit.sendwhatmsg_instantly(
            cleaned, message,
            wait_time=wait_time,
            tab_close=tab_close,
            close_time=close_time
        )
    except Exception as e:
        print(f"[WhatsApp Error] {e}")


def send_message(phone: str, message: str, async_send: bool = True) -> bool:
    """
    Send a WhatsApp message via pywhatkit (opens WhatsApp Web).
    async_send=True sends in background thread so UI doesn't block.
    """
    if not phone or not message:
        return False
    if async_send:
        t = threading.Thread(
            target=_send_whatsapp_background,
            args=(phone, message),
            daemon=True
        )
        t.start()
        return True
    else:
        try:
            _send_whatsapp_background(phone, message)
            return True
        except Exception:
            return False


# ─── Message formatters ────────────────────────────────────────────────────────

def format_reminder_message(template: str, name: str, due_date: str = "") -> str:
    return template.replace("{name}", name).replace("{due_date}", due_date)


def format_removal_message(template: str, name: str) -> str:
    return template.replace("{name}", name)


def format_3day_message(template: str, name: str, due_date: str) -> str:
    return template.replace("{name}", name).replace("{due_date}", due_date)


def format_1day_message(template: str, name: str, due_date: str) -> str:
    return template.replace("{name}", name).replace("{due_date}", due_date)
