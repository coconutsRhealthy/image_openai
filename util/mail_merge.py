import json
import logging
import time

import requests

from util.labels import load_spotted_promotions, save_spotted_promotions

logger = logging.getLogger(__name__)

# The newsletter feed, produced by the claude_diski_mail tool — a separate
# single-writer source. We fold its new deals into spotted_promotions.json here
# so that every consumer reads only that one file.
MAIL_FEED_URL = "https://pub-a3be569620e4415b916e737210363aee.r2.dev/spotted_mails.json"


def _key(entry: dict) -> tuple:
    """Identity of a deal, for skipping ones already in spotted_promotions.json."""
    return (entry.get("webshop_name"), entry.get("date"), entry.get("korting_text_nl"))


def merge_spotted_mails() -> int:
    """Fold new newsletter deals into spotted_promotions.json. Returns count added.

    - Deals flagged also_on_homepage are skipped: the same deal is already spotted
      here, so merging it would duplicate it.
    - Deals already present (webshop_name + date + korting_text_nl) are skipped, so
      this is idempotent and safe to run every cycle — it only writes when there is
      something genuinely new.
    - New ones are tagged from_newsletter (for the frontend label) and prepended,
      newest first.

    Best-effort: any failure is logged and swallowed so the screenshot pipeline is
    never blocked by a hiccup in the newsletter feed.
    """
    try:
        resp = requests.get(f"{MAIL_FEED_URL}?t={int(time.time())}", timeout=10)
        resp.raise_for_status()
        mails = resp.json()
    except Exception as e:
        logger.warning(f"[mail] could not fetch spotted_mails.json: {e}")
        return 0
    if not isinstance(mails, list) or not mails:
        return 0

    try:
        existing = load_spotted_promotions()
    except Exception as e:
        logger.warning(f"[mail] could not load spotted_promotions.json: {e}")
        return 0

    seen = {_key(e) for e in existing}
    fresh = []
    for e in mails:
        if e.get("also_on_homepage"):
            continue
        if _key(e) in seen:
            continue
        entry = {k: v for k, v in e.items() if k != "also_on_homepage"}
        entry["from_newsletter"] = True
        fresh.append(entry)
        seen.add(_key(e))

    if not fresh:
        logger.info("[mail] no new newsletter deals to merge")
        return 0

    try:
        save_spotted_promotions(fresh + existing)
    except Exception as e:
        logger.warning(f"[mail] could not save merged spotted_promotions.json: {e}")
        return 0

    logger.info(f"[mail] merged {len(fresh)} newsletter deal(s) into spotted_promotions.json")
    return len(fresh)
