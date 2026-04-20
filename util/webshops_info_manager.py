import json
import os
import requests
import boto3

import config

ADD_URL = "https://pub-a3be569620e4415b916e737210363aee.r2.dev/webshops_info/webshops_to_add.json"
EXPORT_URL = "https://pub-a3be569620e4415b916e737210363aee.r2.dev/webshops_info/webshop_info_export.json"
EXPORT_KEY = "webshops_info/webshop_info_export.json"


def _get_r2_client():
    return boto3.client(
        "s3",
        endpoint_url=f"https://{config.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=config.R2_ACCESS_KEY,
        aws_secret_access_key=config.R2_SECRET_KEY,
    )


def load_webshop_info() -> dict[str, str]:
    """Returns dict of lowercase shop name -> url."""
    try:
        response = requests.get(EXPORT_URL, timeout=10)
        response.raise_for_status()
        webshops = response.json()
        return {w["name"].lower(): w["url"] for w in webshops if w.get("name") and w.get("url")}
    except Exception as e:
        print(f"Could not load webshop info: {e}")
        return {}


def update_webshops():
    """Merge webshops_to_add.json into webshop_info_export.json and upload to R2."""
    # Load current export
    current = []
    try:
        response = requests.get(EXPORT_URL, timeout=10)
        response.raise_for_status()
        current = response.json()
    except Exception:
        pass

    existing_urls = {w["url"].rstrip("/").lower() for w in current if w.get("url")}

    # Fetch new webshops to add
    try:
        response = requests.get(ADD_URL, timeout=10)
        response.raise_for_status()
        to_add = response.json().get("webshops", [])
    except Exception as e:
        print(f"Could not fetch webshops_to_add: {e}")
        return

    added = 0
    for shop in to_add:
        name = shop.get("name", "").strip()
        url = shop.get("url", "").strip()
        if not name or not url:
            continue
        if url.rstrip("/").lower() not in existing_urls:
            current.append({"name": name, "url": url})
            existing_urls.add(url.rstrip("/").lower())
            added += 1
            print(f"Added webshop: {name} ({url})")

    if added == 0:
        return

    # Upload updated export to R2
    r2 = _get_r2_client()
    r2.put_object(
        Bucket=config.PROMOTIONS_BUCKET,
        Key=EXPORT_KEY,
        Body=json.dumps(current, ensure_ascii=False, indent=2).encode(),
        ContentType="application/json",
    )
    print(f"Uploaded updated webshop_info_export.json ({len(current)} shops, +{added} new)")
