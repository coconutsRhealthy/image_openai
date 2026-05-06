import logging
import time

import requests

import config
from util.labels import REASON_TAGS, set_label

logging.basicConfig(level=logging.INFO, format="%(asctime)s | [bot] %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

API_BASE = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}" if config.TELEGRAM_BOT_TOKEN else None
POLL_TIMEOUT = 30

REASON_BUTTON_LABELS = {
    "first-order": "First-order",
    "newsletter": "Newsletter",
    "free-shipping": "Free shipping",
    "student": "Student",
    "not-a-promo": "Not a promo",
    "other": "Other",
}


def _api(method: str, **payload):
    try:
        r = requests.post(f"{API_BASE}/{method}", json=payload, timeout=POLL_TIMEOUT + 10)
        if not r.ok:
            logger.warning(f"{method} failed: {r.status_code} {r.text}")
            return None
        return r.json()
    except Exception as e:
        logger.warning(f"{method} error: {e}")
        return None


def _reason_keyboard(entry_id: str) -> dict:
    rows, row = [], []
    for tag in REASON_TAGS:
        row.append({"text": REASON_BUTTON_LABELS.get(tag, tag), "callback_data": f"b:{tag}:{entry_id}"})
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return {"inline_keyboard": rows}


def _resolve(chat_id, message_id, original_text, suffix):
    _api(
        "editMessageText",
        chat_id=chat_id,
        message_id=message_id,
        text=f"{original_text}\n\n{suffix}",
        reply_markup={"inline_keyboard": []},
    )


def handle_callback(cb: dict):
    from_id = str(cb.get("from", {}).get("id", ""))
    if from_id != str(config.TELEGRAM_CHAT_ID):
        _api("answerCallbackQuery", callback_query_id=cb["id"], text="unauthorized")
        return

    data = cb.get("data", "")
    msg = cb.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    msg_id = msg.get("message_id")
    original_text = msg.get("text", "")

    if data.startswith("g:"):
        entry_id = data[2:]
        ok = set_label(entry_id, "good")
        _api("answerCallbackQuery", callback_query_id=cb["id"], text="👍" if ok else "entry not found")
        if ok:
            _resolve(chat_id, msg_id, original_text, "✅ Labeled 👍")

    elif data.startswith("down:"):
        entry_id = data[5:]
        _api("answerCallbackQuery", callback_query_id=cb["id"])
        _api(
            "editMessageReplyMarkup",
            chat_id=chat_id,
            message_id=msg_id,
            reply_markup=_reason_keyboard(entry_id),
        )

    elif data.startswith("b:"):
        reason, _, entry_id = data[2:].partition(":")
        if reason not in REASON_TAGS:
            _api("answerCallbackQuery", callback_query_id=cb["id"], text="unknown reason")
            return
        ok = set_label(entry_id, {"bad": reason})
        _api("answerCallbackQuery", callback_query_id=cb["id"], text=f"👎 {reason}" if ok else "entry not found")
        if ok:
            _resolve(chat_id, msg_id, original_text, f"❌ Labeled 👎 {reason}")

    else:
        _api("answerCallbackQuery", callback_query_id=cb["id"], text="unknown action")


def run():
    if not API_BASE or not config.TELEGRAM_CHAT_ID:
        logger.error("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set; bot will not start")
        return

    logger.info("Bot started, long-polling for updates")
    offset = None
    while True:
        try:
            params = {"timeout": POLL_TIMEOUT}
            if offset is not None:
                params["offset"] = offset
            r = requests.get(f"{API_BASE}/getUpdates", params=params, timeout=POLL_TIMEOUT + 10)
            r.raise_for_status()
            for upd in r.json().get("result", []):
                offset = upd["update_id"] + 1
                if "callback_query" in upd:
                    handle_callback(upd["callback_query"])
        except Exception as e:
            logger.warning(f"poll error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    run()
