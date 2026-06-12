import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import boto3
from botocore.exceptions import ClientError
from openai import OpenAI

import config
from util.labels import load_spotted_promotions, make_entry_id, save_spotted_promotions

logger = logging.getLogger(__name__)

_client = OpenAI(api_key=config.OPENAI_API_KEY)

DATE_FMT = "%Y-%m-%d %H:%M:%S"

# Audit log of removed duplicates (newest-first), in the promotions bucket.
DEDUP_LOG_KEY = "dedup_removed.json"


def _get_r2_client():
    return boto3.client(
        "s3",
        endpoint_url=f"https://{config.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=config.R2_ACCESS_KEY,
        aws_secret_access_key=config.R2_SECRET_KEY,
    )


def _log_record(removed: dict, removed_id: str, original: dict, original_id: str) -> dict:
    now = datetime.now(ZoneInfo("Europe/Amsterdam"))
    return {
        "removed_at": now.strftime(DATE_FMT),
        "webshop_name": removed.get("webshop_name", "-"),
        "removed_entry": {**removed, "entry_id": removed_id},
        "duplicate_of": {
            "entry_id": original_id,
            "date": original.get("date"),
            "korting_text": original.get("korting_text"),
            "korting_text_nl": original.get("korting_text_nl"),
        },
    }


def _append_removal_log(records: list[dict]) -> None:
    """Prepend removal records to dedup_removed.json in R2. Best-effort caller decides."""
    if not records:
        return
    r2 = _get_r2_client()
    try:
        obj = r2.get_object(Bucket=config.PROMOTIONS_BUCKET, Key=DEDUP_LOG_KEY)
        existing = json.loads(obj["Body"].read())
        if not isinstance(existing, list):
            existing = []
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") in ("NoSuchKey", "404"):
            existing = []
        else:
            raise

    existing = list(records) + existing
    r2.put_object(
        Bucket=config.PROMOTIONS_BUCKET,
        Key=DEDUP_LOG_KEY,
        Body=json.dumps(existing, ensure_ascii=False, indent=2).encode("utf-8"),
        ContentType="application/json",
    )

# NOTE: prompt is a first draft — tune the duplicate criteria later.
PROMPT = """You are deduplicating recorded promotion entries for the Dutch webshop "{shop}".

Each entry below is one time a promotion was spotted on this webshop's homepage. The same
promotion is often spotted again on later days, and the wording recorded each time can
differ. Your job is to group the entries that point at the SAME real-world promotion.

Below are recent promotions recorded for this webshop (newest first):
{entries}

Two entries belong in the same group when they clearly refer to the same offer. They do
NOT need identical wording — judge the underlying promotion, not the exact text. Treat as
the same promotion when they match on the substance of the deal, for example:
- the same discount (e.g. "20% korting op alles" and "nu 20% korting op het hele assortiment")
- the same promo code (e.g. "code ELLE20 voor 20% korting" and "20% met de code ELLE20")
- the same gift or deal (e.g. "3 samples cadeau vanaf €60" and "gratis 3 parfum samples bij €60+")
Ignore differences in phrasing, language, punctuation, casing, word order, emoji, or how
long the summary is.

Keep entries in SEPARATE groups when they are genuinely different offers — a different
discount percentage, a different code, a different gift, or a clearly different product
scope (e.g. "20% op alles" vs "20% op schoenen") — even if the wording looks similar.

Only output groups that contain two or more ids. Entries with no duplicate are left out.

Respond with JSON only:
{{
  "duplicate_groups": [
    ["id-a", "id-b"],
    ["id-c", "id-d", "id-e"]
  ]
}}"""


def _entry_text(entry: dict) -> str:
    return entry.get("korting_text_nl") or entry.get("korting_text") or "-"


def _parse_dt(value) -> "datetime | None":
    try:
        return datetime.strptime(value, DATE_FMT)
    except (TypeError, ValueError):
        return None


def _find_duplicate_groups(shop: str, entries: list[dict]) -> "tuple[list[list[str]], dict[str, dict]]":
    """Ask the model to cluster same-offer entries for one shop.

    Returns (groups, by_id) where groups is a list of id-lists (each 2+ valid ids) and
    by_id maps entry-id -> entry.
    """
    by_id: dict[str, dict] = {}
    lines = []
    for e in entries:
        eid = make_entry_id(e.get("webshop_name", ""), e.get("date", ""))
        by_id[eid] = e
        lines.append(f'- id={eid} | {e.get("date", "?")} | "{_entry_text(e)}"')

    prompt = PROMPT.format(shop=shop, entries="\n".join(lines))
    response = _client.chat.completions.create(
        model=config.OPENAI_MODEL,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("dedup: could not parse OpenAI response as JSON: %s", raw)
        return [], by_id

    groups = []
    for group in result.get("duplicate_groups") or []:
        ids = [i for i in group if i in by_id]
        if len(ids) >= 2:
            groups.append(ids)
    return groups, by_id


def _removals(groups: list[list[str]], by_id: dict[str, dict]) -> "list[tuple[str, str]]":
    """For each duplicate group, keep the earliest (the original) and remove every later
    copy recorded less than DEDUP_WINDOW_DAYS after it. Later copies beyond the window are
    kept (treated as a legitimate re-run of the offer).

    Returns a list of (removed_id, original_id) pairs."""
    pairs: list[tuple[str, str]] = []
    window = timedelta(days=config.DEDUP_WINDOW_DAYS)

    for ids in groups:
        dated = [(_parse_dt(by_id[i].get("date")), i) for i in ids]
        dated = [(dt, i) for dt, i in dated if dt is not None]
        if len(dated) < 2:
            continue
        dated.sort(key=lambda x: x[0])

        original_dt, original_id = dated[0]
        for dt, eid in dated[1:]:
            if dt - original_dt < window:
                pairs.append((eid, original_id))
            else:
                logger.info(
                    "dedup: '%s' duplicates an entry older than %d days — keeping it",
                    _entry_text(by_id[eid]), config.DEDUP_WINDOW_DAYS,
                )
    return pairs


def run_sweep() -> int:
    """Scan the newest DEDUP_RECENT_COUNT spotted promotions, remove recent duplicates,
    and re-upload spotted_promotions.json. Returns the number of entries removed."""
    if not config.DEDUP_ENABLED:
        logger.info("dedup sweep disabled (DEDUP_ENABLED=False)")
        return 0

    all_entries = load_spotted_promotions()
    if not all_entries:
        logger.info("dedup sweep: spotted_promotions.json empty; nothing to do")
        return 0

    recent = all_entries[:config.DEDUP_RECENT_COUNT]
    by_shop: dict[str, list[dict]] = defaultdict(list)
    for e in recent:
        by_shop[e.get("webshop_name", "").lower()].append(e)

    to_remove: set = set()
    log_records: list[dict] = []
    for shop, entries in by_shop.items():
        if len(entries) < 2:
            continue
        groups, by_id = _find_duplicate_groups(shop, entries)
        for removed_id, original_id in _removals(groups, by_id):
            logger.info("dedup sweep: removing duplicate %s ('%s')",
                        removed_id, _entry_text(by_id[removed_id]))
            log_records.append(_log_record(by_id[removed_id], removed_id, by_id[original_id], original_id))
            to_remove.add(removed_id)

    if not to_remove:
        logger.info("dedup sweep: no removable duplicates found in newest %d entries",
                    len(recent))
        return 0

    kept = [
        e for e in all_entries
        if make_entry_id(e.get("webshop_name", ""), e.get("date", "")) not in to_remove
    ]
    removed = len(all_entries) - len(kept)
    save_spotted_promotions(kept)
    logger.info("dedup sweep: removed %d duplicate entr%s", removed, "y" if removed == 1 else "ies")

    try:
        _append_removal_log(log_records)
    except Exception as e:
        logger.warning(f"dedup sweep: could not write removal log: {e}")

    return removed
