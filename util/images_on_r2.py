import boto3
from datetime import datetime
import os  # nodig voor os.path.basename

# ======================
# CONFIG
# ======================
R2_ACCOUNT_ID = "secret"
R2_ACCESS_KEY = "secret"
R2_SECRET_KEY = "secret"
BUCKET_NAME = "screenshots"
START_DATE = "2026-01-01"
OUTPUT_FILE = "output_aaa_r2_01.txt"

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")
R2_ENDPOINT = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

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

    results = []

    # ÉÉN LIST call per pagina, direct filteren
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix=""):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if not key.lower().endswith(IMAGE_EXTENSIONS):
                continue
            if obj["LastModified"].replace(tzinfo=None) < start_date:
                continue

            # haal filename uit key
            filename = os.path.basename(key)
            webshop = filename.split("_")[0]  # alles voor eerste underscore

            results.append(f"{webshop} - {filename}")

    # schrijf output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(results))

    print(f"Klaar! {len(results)} regels geschreven naar {OUTPUT_FILE}")


if __name__ == "__main__":
    main()