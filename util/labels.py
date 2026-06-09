import json
import logging

import boto3
from botocore.exceptions import ClientError

import config

logger = logging.getLogger(__name__)

SPOTTED_PROMOTIONS_KEY = "spotted_promotions.json"

REASON_TAGS = [
    "first-order",
    "newsletter",
    "free-shipping",
    "student",
    "not-a-promo",
    "other",
]


def _get_r2_client():
    return boto3.client(
        "s3",
        endpoint_url=f"https://{config.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=config.R2_ACCESS_KEY,
        aws_secret_access_key=config.R2_SECRET_KEY,
    )


def make_entry_id(webshop_name: str, date_str: str) -> str:
    """Stable ID for a promotion entry. date_str is 'YYYY-MM-DD HH:MM:SS' (Europe/Amsterdam)."""
    compact = date_str.replace("-", "").replace(" ", "").replace(":", "")
    return f"{webshop_name}_{compact}"


def entry_id_to_day(entry_id: str) -> str:
    """Day ('YYYY-MM-DD') of an entry id produced by make_entry_id."""
    compact = entry_id.rpartition("_")[2]
    return f"{compact[0:4]}-{compact[4:6]}-{compact[6:8]}"


def load_spotted_promotions() -> list[dict]:
    """Load full spotted_promotions.json from R2. Returns empty list if missing."""
    r2 = _get_r2_client()
    try:
        obj = r2.get_object(Bucket=config.PROMOTIONS_BUCKET, Key=SPOTTED_PROMOTIONS_KEY)
        data = json.loads(obj["Body"].read())
        if not isinstance(data, list):
            raise ValueError(f"{SPOTTED_PROMOTIONS_KEY} is not a list")
        return data
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") in ("NoSuchKey", "404"):
            return []
        raise


def set_label(entry_id: str, label) -> bool:
    """Find entry by ID and set its label. Returns True if updated, False if not found."""
    r2 = _get_r2_client()
    try:
        obj = r2.get_object(Bucket=config.PROMOTIONS_BUCKET, Key=SPOTTED_PROMOTIONS_KEY)
        entries = json.loads(obj["Body"].read())
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") in ("NoSuchKey", "404"):
            return False
        raise

    updated = False
    for entry in entries:
        if make_entry_id(entry.get("webshop_name", ""), entry.get("date", "")) == entry_id:
            entry["label"] = label
            updated = True
            break

    if not updated:
        return False

    r2.put_object(
        Bucket=config.PROMOTIONS_BUCKET,
        Key=SPOTTED_PROMOTIONS_KEY,
        Body=json.dumps(entries, ensure_ascii=False, indent=2).encode("utf-8"),
        ContentType="application/json",
    )
    return True
