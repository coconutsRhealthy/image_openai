import os
import re
from db.db_connection import get_database_connection
from datetime import datetime
import boto3

# ======================
# CONFIG (R2)
# ======================
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY")
R2_SECRET_KEY = os.getenv("R2_SECRET_KEY")

BUCKET_NAME = "screenshots"
R2_ENDPOINT = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"


# ======================
# S3 CLIENT
# ======================
def get_s3():
    return boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY
    )


# ======================
# DB
# ======================
def get_webshop_name(webshop_id):
    with get_database_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT webshop_name FROM webshop_info WHERE id = %s",
            (webshop_id,)
        )
        row = cursor.fetchone()

        if not row:
            raise ValueError(f"Webshop with id {webshop_id} not found")

        return row[0]


# ======================
# R2 FILES (FILTERED)
# ======================
def get_files_for_webshop(webshop_name):
    """
    Returns:
        list[str] -> filenames (unsorted)
    """
    s3 = get_s3()

    files = []
    prefix = f"{webshop_name}_"

    paginator = s3.get_paginator("list_objects_v2")

    for page in paginator.paginate(
            Bucket=BUCKET_NAME,
            Prefix=prefix
    ):
        for obj in page.get("Contents", []):
            files.append(obj["Key"])

    return files


# ======================
# DATETIME PARSING
# ======================
def extract_datetime(filename, webshop_name):
    """
    Example:
        zalando_20260301_204326.jpg
    """
    pattern = rf"^{re.escape(webshop_name)}_(\d{{8}})_(\d{{6}})"

    match = re.match(pattern, filename)
    if not match:
        return None

    dt_str = match.group(1) + match.group(2)

    return datetime.strptime(dt_str, "%Y%m%d%H%M%S")


# ======================
# MAIN LOGIC
# ======================
def get_sorted_screenshots(webshop_id):
    webshop_name = get_webshop_name(webshop_id)

    files = get_files_for_webshop(webshop_name)

    parsed = []

    for f in files:
        dt = extract_datetime(f, webshop_name)
        if dt:
            parsed.append((f, dt))

    # newest -> oldest
    parsed.sort(key=lambda x: x[1], reverse=True)

    return [f[0] for f in parsed]

# ======================
# PUBLIC METHOD
# ======================
def get_latest_screenshot_urls(webshop_id, amount):
    """
    Returns:
        list[str] -> public URLs (newest -> oldest)
    """
    webshop_name = get_webshop_name(webshop_id)

    files = get_files_for_webshop(webshop_name)

    parsed = []

    for f in files:
        dt = extract_datetime(f, webshop_name)
        if dt:
            parsed.append((f, dt))

    # sort newest -> oldest
    parsed.sort(key=lambda x: x[1], reverse=True)

    # limit
    limited = parsed[:amount]

    base_url = "https://pub-f75dabf2f86f4ad4ba4765ede21e47cc.r2.dev/"

    # build urls
    urls = [
        f"{base_url}{filename}"
        for (filename, _) in limited
    ]

    return urls

# ======================
# RUN
# ======================
if __name__ == "__main__":
    webshop_id = 37  # input

    files = get_latest_screenshot_urls(webshop_id, 2)

    for f in files:
        print(f)