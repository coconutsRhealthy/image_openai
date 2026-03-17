import os
import json
import requests
import boto3
from db.db_connection import get_database_connection

JSON_URL = "https://pub-a3be569620e4415b916e737210363aee.r2.dev/webshops_info/webshops_to_add.json"

def normalize_url(url):
    """Verwijdert trailing slash en zet URL lowercase voor consistente checks."""
    return url.rstrip("/").lower()

def upload_to_r2(file_path, r2_filename):
    """Upload een bestand naar Cloudflare R2."""
    r2 = boto3.client(
        "s3",
        endpoint_url=f"https://{os.getenv('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
        aws_access_key_id=os.getenv("R2_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("R2_SECRET_KEY"),
    )

    with open(file_path, "rb") as f:
        r2.put_object(
            Bucket="promotions",
            Key=f"webshops_info/{r2_filename}",
            Body=f,
            ContentType="application/json",
        )
    print(f"☁️ Uploaded {r2_filename} to R2")

def update_webshops_and_export():
    """Haalt JSON op, update database, en exporteert volledige tabel naar R2."""
    # --- Step 1: JSON ophalen ---
    try:
        response = requests.get(JSON_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Fout bij ophalen/parsen JSON: {e}")
        return

    webshops = data.get("webshops", [])
    if not webshops:
        print("Geen webshops gevonden in JSON.")
        return

    added = 0
    with get_database_connection() as db:
        cursor = db.cursor()
        # Bestaande URLs ophalen
        cursor.execute("SELECT webshop_url FROM webshop_info")
        existing_urls = set(normalize_url(url[0]) for url in cursor.fetchall())

        insert_query = "INSERT INTO webshop_info (webshop_name, webshop_url) VALUES (%s, %s)"

        for shop in webshops:
            name = shop.get("name", "").strip()
            url = shop.get("url", "").strip()
            if not name or not url:
                continue  # skip lege entries

            url_normalized = normalize_url(url)
            if url_normalized not in existing_urls:
                cursor.execute(insert_query, (name, url))
                db.commit()
                added += 1
                existing_urls.add(url_normalized)
                print(f"Nieuwe webshop toegevoegd: {name} ({url})")

        print(f"Totaal nieuwe webshops toegevoegd: {added}")

        # --- Step 2: volledige tabel exporteren ---
        cursor.execute("SELECT id, webshop_name, webshop_url FROM webshop_info ORDER BY id")
        rows = cursor.fetchall()
        export_list = [{"id": r[0], "name": r[1], "url": r[2]} for r in rows]

        json_filename = "webshop_info_export.json"
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(export_list, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON export gemaakt: {json_filename}")

    # --- Step 3: upload naar R2 ---
    upload_to_r2(json_filename, json_filename)

if __name__ == "__main__":
    update_webshops_and_export()