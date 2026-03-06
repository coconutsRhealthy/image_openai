import boto3
from datetime import datetime
import os
import re

# ======================
# CONFIG
# ======================
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY")
R2_SECRET_KEY = os.getenv("R2_SECRET_KEY")
BUCKET_NAME = "screenshots"
START_DATE = "2026-03-05"

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")
R2_ENDPOINT = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

# regex om datum+tijd uit filename te halen: voorbeeld adidas_20260226_041659.jpg
FILENAME_TIMESTAMP_REGEX = re.compile(r".*_(\d{8})_(\d{6})")

# ======================
# MAIN
# ======================
def get_filenames_on_r2_per_webshop() -> dict[str, list[str]]:
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

    # Zet alles om naar dict[webshop] = lijst van filenames (gesorteerd op datetime)
    filename_screenshot_dict = {
        webshop: [fname for _, fname in sorted(files, key=lambda x: x[0])]
        for webshop, files in webshop_files.items()
    }

    total = sum(len(v) for v in filename_screenshot_dict.values())
    print(f"Klaar! {total} bestanden gevonden.")

    return filename_screenshot_dict


if __name__ == "__main__":
    get_filenames_on_r2_per_webshop()