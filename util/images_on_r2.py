import boto3
from datetime import datetime
import os
import re

# ======================
# CONFIG
# ======================
R2_ACCOUNT_ID = "secret"
R2_ACCESS_KEY = "secret"
R2_SECRET_KEY = "secret"
BUCKET_NAME = "screenshots"
START_DATE = "2026-01-01"
OUTPUT_FILE = "output_aaa_r2_02.txt"

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")
R2_ENDPOINT = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

# regex om datum+tijd uit filename te halen: voorbeeld adidas_20260226_041659.jpg
FILENAME_TIMESTAMP_REGEX = re.compile(r".*_(\d{8})_(\d{6})")

# ======================
# MAIN
# ======================
def main():
    start_date = datetime.strptime(START_DATE, "%Y-%m-%d")

    s3 = boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
    )

    webshop_files = {}

    # ÉÉN LIST call per pagina
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix=""):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if not key.lower().endswith(IMAGE_EXTENSIONS):
                continue

            # haal filename en webshop
            filename = os.path.basename(key)
            webshop = filename.split("_")[0]

            # datum+tijd uit filename
            match = FILENAME_TIMESTAMP_REGEX.match(filename)
            if not match:
                continue  # skip bestanden zonder correcte timestamp

            date_str, time_str = match.groups()
            file_datetime = datetime.strptime(date_str + time_str, "%Y%m%d%H%M%S")
            if file_datetime < start_date:
                continue

            # voeg toe aan dict per webshop
            if webshop not in webshop_files:
                webshop_files[webshop] = []
            webshop_files[webshop].append((file_datetime, filename))

    # schrijf output, gesorteerd op datum per webshop
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for webshop in sorted(webshop_files.keys()):
            for _, filename in sorted(webshop_files[webshop], key=lambda x: x[0]):
                f.write(f"{webshop} - {filename}\n")

    total = sum(len(v) for v in webshop_files.values())
    print(f"Klaar! {total} regels geschreven naar {OUTPUT_FILE}")


if __name__ == "__main__":
    main()