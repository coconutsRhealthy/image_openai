from collections import defaultdict
from datetime import datetime, timedelta

WINDOW_DAYS = 14
MAX_PER_CATEGORY = 3

REASON_LABELS = {
    "first-order": "First-order / new-customer discounts",
    "newsletter": "Newsletter sign-up incentives",
    "free-shipping": "Free shipping offers",
    "student": "Student discounts",
    "not-a-promo": "Not actually promotions",
    "other": "Other flagged noise",
}


def _extract_bad_reason(label) -> "str | None":
    if isinstance(label, dict) and "bad" in label:
        return label["bad"]
    return None


def build_dynamic_ignore_block(entries: list[dict], now: datetime = None) -> str:
    """Build the dynamic IGNORE prompt section from labeled-bad entries.

    Returns empty string if no relevant labels.
    """
    now = now or datetime.now()
    cutoff = now - timedelta(days=WINDOW_DAYS)

    by_reason: dict[str, list[tuple[datetime, str]]] = defaultdict(list)

    for entry in entries:
        reason = _extract_bad_reason(entry.get("label"))
        if not reason:
            continue
        try:
            entry_dt = datetime.strptime(entry["date"], "%Y-%m-%d %H:%M:%S")
        except (KeyError, ValueError):
            continue
        if entry_dt < cutoff:
            continue
        text = entry.get("korting_text") or entry.get("korting_text_nl")
        if not text or text == "-":
            continue
        by_reason[reason].append((entry_dt, text))

    if not by_reason:
        return ""

    lines = ["Recently flagged as noise by the operator (do NOT report similar):"]
    for reason in REASON_LABELS:
        items = by_reason.get(reason)
        if not items:
            continue
        items.sort(key=lambda x: x[0], reverse=True)
        examples = "; ".join(f'"{text}"' for _, text in items[:MAX_PER_CATEGORY])
        lines.append(f"- {REASON_LABELS[reason]}: {examples}")

    return "\n".join(lines)
