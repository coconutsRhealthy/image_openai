import json
import os
import boto3
import mysql.connector
from datetime import datetime
from zoneinfo import ZoneInfo

from db.webshops_db_access import get_webshop_name_and_url
from util.json_util import get_offer


def shorten_text(text: str, max_words: int = 15) -> str:
    if not text:
        return "-"
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "…"


def append_and_upload(json_entries):
    if not json_entries:
        return

    now_amsterdam = datetime.now(ZoneInfo("Europe/Amsterdam"))
    date_str = now_amsterdam.strftime("%Y-%m-%d")

    ndjson_filename = f"{date_str}.ndjson"
    json_filename = f"{date_str}.json"

    ndjson_path = os.path.join("/data", ndjson_filename)
    json_path = os.path.join("/data", json_filename)

    # ---- lokaal NDJSON appenden ----

    with open(ndjson_path, "a", encoding="utf-8") as f:
        for entry in json_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # ---- NDJSON -> JSON array genereren ----

    objects = []

    with open(ndjson_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                objects.append(json.loads(line))

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(objects, f, ensure_ascii=False, indent=2)

    # ---- R2 client ----

    r2 = boto3.client(
        "s3",
        endpoint_url=f"https://{os.getenv('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
        aws_access_key_id=os.getenv("R2_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("R2_SECRET_KEY"),
    )

    # ---- upload NDJSON ----

    with open(ndjson_path, "rb") as f:
        r2.put_object(
            Bucket="promotions",
            Key=f"ndjson/{ndjson_filename}",
            Body=f,
            ContentType="application/x-ndjson",
        )

    # ---- upload JSON ----

    with open(json_path, "rb") as f:
        r2.put_object(
            Bucket="promotions",
            Key=f"json/{json_filename}",
            Body=f,
            ContentType="application/json",
        )

    print(f"✅ Appended {len(json_entries)} entries")
    print(f"☁️ Uploaded {ndjson_filename} and {json_filename} to R2")


def export_new_offers_for_screenshot(webshop_id: int, screenshot_id: int, novelty_analysis_json: str):
    webshop_name, webshop_url = get_webshop_name_and_url(webshop_id)

    try:
        novelty_analysis = json.loads(novelty_analysis_json)
    except json.JSONDecodeError:
        print(f"⚠️ Invalid novelty_analysis JSON for screenshot {screenshot_id}")
        return

    offers = novelty_analysis.get("offers")

    if not isinstance(offers, list):
        return

    new_offers = [
        offer for offer in offers
        if offer.get("is_new") is True
    ]

    if not new_offers:
        print("No new offers found.")
        return

    now_amsterdam = datetime.now(ZoneInfo("Europe/Amsterdam"))

    json_entries = []

    for novelty_offer in new_offers:

        offer_text = novelty_offer.get("novelty_summary_nl")

        if not offer_text:
            continue

        entry = {
            "webshop_name": webshop_name,
            "url": webshop_url or "-",
            "korting_text": offer_text,
            "korting_text_nl": offer_text,
            "date": now_amsterdam.strftime("%Y-%m-%d %H:%M:%S")
        }

        json_entries.append(entry)

    append_and_upload(json_entries)


# -------------------------
# TEST RUNNER
# -------------------------

def get_test_record(screenshot_id: int):

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="py_diski_webshops"
    )

    query = """
        SELECT
            d.webshop_id,
            d.screenshot_id,
            d.novelty_analysis
        FROM detected_discounts d
        WHERE d.screenshot_id = %s
        LIMIT 1
    """

    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, (screenshot_id,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    return row


if __name__ == "__main__":

    TEST_SCREENSHOT_ID = 1967  # pas aan

    row = get_test_record(TEST_SCREENSHOT_ID)

    if not row:
        print("❌ No detected_discounts entry found.")
    else:
        export_new_offers_for_screenshot(
            webshop_id=row["webshop_id"],
            screenshot_id=row["screenshot_id"],
            novelty_analysis_json=row["novelty_analysis"]
        )