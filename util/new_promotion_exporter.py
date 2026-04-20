import json
import os
import boto3
from datetime import datetime
from zoneinfo import ZoneInfo

import config


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

    print(f"Exported {len(entries)} new promotion(s) to R2 ({date_str})")


def export_new_promotion(webshop_name: str, webshop_url: str, result: dict):
    now = datetime.now(ZoneInfo("Europe/Amsterdam"))
    entry = {
        "webshop_name": webshop_name,
        "url": webshop_url or "-",
        "korting_text": _shorten_text(result.get("promo_original") or "-"),
        "korting_text_nl": result.get("promo_nl_summ") or "-",
        "confidence": result.get("confidence", "unknown"),
        "date": now.strftime("%Y-%m-%d %H:%M:%S"),
    }
    _append_and_upload([entry])
