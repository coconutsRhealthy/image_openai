import json
import logging
import os
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
from zoneinfo import ZoneInfo

import config
from util.labels import entry_id_to_day, make_entry_id
from util.telegram_notify import send_new_promo_message

logger = logging.getLogger(__name__)

SPOTTED_PROMOTIONS_KEY = "spotted_promotions.json"


def _shorten_text(text: str, max_words: int = 15) -> str:
    if not text:
        return "-"
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "…"


def _get_r2_client():
    return boto3.client(
        "s3",
        endpoint_url=f"https://{config.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=config.R2_ACCESS_KEY,
        aws_secret_access_key=config.R2_SECRET_KEY,
    )


def _append_and_upload(entries: list[dict]):
    if not entries:
        return

    now = datetime.now(ZoneInfo("Europe/Amsterdam"))
    date_str = now.strftime("%Y-%m-%d")

    ndjson_path = os.path.join("/data", f"{date_str}.ndjson")
    json_path = os.path.join("/data", f"{date_str}.json")

    with open(ndjson_path, "a", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    all_entries = []
    with open(ndjson_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                all_entries.append(json.loads(line))

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, ensure_ascii=False, indent=2)

    r2 = _get_r2_client()

    with open(ndjson_path, "rb") as f:
        r2.put_object(
            Bucket=config.PROMOTIONS_BUCKET,
            Key=f"ndjson/{date_str}.ndjson",
            Body=f,
            ContentType="application/x-ndjson",
        )

    with open(json_path, "rb") as f:
        r2.put_object(
            Bucket=config.PROMOTIONS_BUCKET,
            Key=f"json/{date_str}.json",
            Body=f,
            ContentType="application/json",
        )

    _append_to_spotted_promotions(r2, entries)

    print(f"Exported {len(entries)} new promotion(s) to R2 ({date_str})")


def _append_to_spotted_promotions(r2, entries: list[dict]):
    try:
        obj = r2.get_object(Bucket=config.PROMOTIONS_BUCKET, Key=SPOTTED_PROMOTIONS_KEY)
        existing = json.loads(obj["Body"].read())
        if not isinstance(existing, list):
            raise ValueError(f"{SPOTTED_PROMOTIONS_KEY} is not a list")
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") in ("NoSuchKey", "404"):
            existing = []
        else:
            raise

    existing = list(entries) + existing
    r2.put_object(
        Bucket=config.PROMOTIONS_BUCKET,
        Key=SPOTTED_PROMOTIONS_KEY,
        Body=json.dumps(existing, ensure_ascii=False, indent=2).encode("utf-8"),
        ContentType="application/json",
    )


def _apply_thumbs_down(entries: list[dict], target_id: str) -> int:
    """Set thumbs_down=True on every entry whose id matches target_id. Returns match count."""
    n = 0
    for entry in entries:
        if make_entry_id(entry.get("webshop_name", ""), entry.get("date", "")) == target_id:
            entry["thumbs_down"] = True
            n += 1
    return n


def mark_thumbs_down_in_daily(entry_id: str):
    """Flag a promotion as thumbs-down in its day's daily files.

    Updates the local /data copy (the source the exporter re-uploads from, so the flag
    survives a same-day re-export) then pushes both files to R2.
    """
    day = entry_id_to_day(entry_id)
    ndjson_path = os.path.join("/data", f"{day}.ndjson")
    json_path = os.path.join("/data", f"{day}.json")
    r2 = _get_r2_client()

    if not os.path.exists(ndjson_path):
        logger.warning("No local daily file %s; cannot flag thumbs-down for %s", ndjson_path, entry_id)
        return

    entries = []
    with open(ndjson_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))

    if not _apply_thumbs_down(entries, entry_id):
        logger.warning("Entry %s not found in local daily file %s", entry_id, ndjson_path)
        return

    with open(ndjson_path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    with open(ndjson_path, "rb") as f:
        r2.put_object(
            Bucket=config.PROMOTIONS_BUCKET,
            Key=f"ndjson/{day}.ndjson",
            Body=f,
            ContentType="application/x-ndjson",
        )
    with open(json_path, "rb") as f:
        r2.put_object(
            Bucket=config.PROMOTIONS_BUCKET,
            Key=f"json/{day}.json",
            Body=f,
            ContentType="application/json",
        )

    logger.info("Marked thumbs-down for %s in daily files (local + R2)", entry_id)


def export_new_promotion(webshop_name: str, webshop_url: str, result: dict):
    now = datetime.now(ZoneInfo("Europe/Amsterdam"))
    entry = {
        "webshop_name": webshop_name,
        "url": webshop_url or "-",
        "korting_text": _shorten_text(result.get("promo_original") or "-"),
        "korting_text_nl": result.get("promo_nl_summ") or "-",
        "date": now.strftime("%Y-%m-%d %H:%M:%S"),
        "label": None,
    }
    _append_and_upload([entry])
    send_new_promo_message(entry)
