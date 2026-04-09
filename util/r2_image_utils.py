import boto3
import os
import re
from collections import defaultdict
from datetime import datetime

# ======================
# CONFIG
# ======================
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY")
R2_SECRET_KEY = os.getenv("R2_SECRET_KEY")
BUCKET_NAME = "screenshots"
R2_ENDPOINT = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
START_DATE = os.getenv("START_DATE", "2026-03-05")
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")
FILENAME_TIMESTAMP_REGEX = re.compile(r".*_(\d{8})_(\d{6})")

# ======================
# S3 CLIENT
# ======================
def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY
    )

# ======================
# FILE METADATA
# ======================
def get_files_with_metadata_per_shop():
    """
    Returns dict[shop -> list[(datetime, filename, size)]]
    """
    start_date = datetime.strptime(START_DATE, "%Y-%m-%d")
    s3 = get_s3_client()
    webshop_files = defaultdict(list)

    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=BUCKET_NAME):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if not key.lower().endswith(IMAGE_EXTENSIONS):
                continue

            filename = os.path.basename(key)
            webshop = filename.split("_")[0]

            match = FILENAME_TIMESTAMP_REGEX.match(filename)
            if not match:
                continue

            date_str, time_str = match.groups()
            file_datetime = datetime.strptime(date_str + time_str, "%Y%m%d%H%M%S")
            if file_datetime < start_date:
                continue

            filesize = obj["Size"]
            webshop_files[webshop].append((file_datetime, filename, filesize))

    # sorteer op datum
    return {shop: sorted(files, key=lambda x: x[0]) for shop, files in webshop_files.items()}

# ======================
# LATEST FILES & INDEX
# ======================
def get_two_latest_files_per_shop(files_per_shop):
    latest_two = {}
    for shop, files in files_per_shop.items():
        latest_two[shop] = files[-2:] if len(files) >= 2 else files
    return latest_two

def build_filename_index(latest_two_map):
    """
    filename -> list of latest two files for shop
    """
    index = {}
    for shop, files in latest_two_map.items():
        for entry in files:
            index[entry[1]] = files
    return index

def calculate_filesize_change_percent(filename, filename_index):
    files = filename_index.get(filename)
    if not files or len(files) < 2:
        return None
    newest, previous = files[-1], files[-2]
    if newest[1] != filename:
        return None
    if previous[2] == 0:
        return None
    return abs(newest[2] - previous[2]) / previous[2] * 100