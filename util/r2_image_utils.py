import boto3
import os
import re
from collections import defaultdict
from datetime import datetime

import config

BUCKET_NAME = config.SCREENSHOTS_BUCKET
R2_ENDPOINT = f"https://{config.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
START_DATE = os.getenv("START_DATE", "2026-03-05")
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")
FILENAME_TIMESTAMP_REGEX = re.compile(r".*_(\d{8})_(\d{6})")


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=config.R2_ACCESS_KEY,
        aws_secret_access_key=config.R2_SECRET_KEY,
    )


def get_files_with_metadata_per_shop() -> dict[str, list[tuple[datetime, str, int]]]:
    """Returns dict[shop -> sorted list of (datetime, filename, size)] oldest first."""
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

            webshop_files[webshop].append((file_datetime, filename, obj["Size"]))

    return {shop: sorted(files, key=lambda x: x[0]) for shop, files in webshop_files.items()}


def download_image_bytes(filename: str) -> bytes:
    s3 = get_s3_client()
    response = s3.get_object(Bucket=BUCKET_NAME, Key=filename)
    return response["Body"].read()
