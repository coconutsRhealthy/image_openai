import logging

import requests

import config
from util.labels import make_entry_id

logger = logging.getLogger(__name__)


def _build_keyboard(entry_id: str) -> dict:
    return {
        "inline_keyboard": [[
            {"text": "👍", "callback_data": f"g:{entry_id}"},
            {"text": "👎", "callback_data": f"down:{entry_id}"},
        ]]
    }


def send_new_promo_message(entry: dict) -> None:
    """Send a Telegram message with 👍/👎 buttons for a new promotion. Best-effort: logs and swallows errors."""
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        logger.warning("Telegram credentials not set; skipping notification")
        return

    entry_id = make_entry_id(entry["webshop_name"], entry["date"])
    text = (
        f"🆕 *{entry['webshop_name']}*\n"
        f"{entry.get('korting_text_nl') or '-'}\n"
        f"_orig:_ {entry.get('korting_text') or '-'}"
    )

    try:
        r = requests.post(
            f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": config.TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": "Markdown",
                "reply_markup": _build_keyboard(entry_id),
            },
            timeout=10,
        )
        if not r.ok:
            logger.warning(f"Telegram sendMessage failed: {r.status_code} {r.text}")
    except Exception as e:
        logger.warning(f"Telegram sendMessage error: {e}")
