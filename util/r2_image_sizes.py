import boto3
import os
from collections import defaultdict


# ======================
# CONFIG
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
# DATA LOADING
# ======================
def get_file_map():
    """
    Returns:
        dict[str, int] -> filename -> filesize
    """
    s3 = get_s3()
    file_map = {}

    paginator = s3.get_paginator("list_objects_v2")

    for page in paginator.paginate(Bucket=BUCKET_NAME):
        for obj in page.get("Contents", []):
            file_map[obj["Key"]] = obj["Size"]

    return file_map


# ======================
# CORE LOGIC
# ======================
def parse_filename(filename):
    """
    Extract shop and timestamp from filename.
    Expected format:
    shop_YYYYMMDD_HHMMSS.png
    """
    try:
        shop, date_part, rest = filename.rsplit("_", 2)
        time_part = rest.split(".")[0]
        timestamp = f"{date_part}{time_part}"
        return shop, timestamp
    except ValueError:
        return None, None


def get_two_latest_per_shop(file_map):
    """
    Returns:
        dict[shop -> [(timestamp, filename, size), ...]]
        Only the two newest files per shop.
    """
    grouped = defaultdict(list)

    for filename, size in file_map.items():
        shop, timestamp = parse_filename(filename)

        if not shop:
            continue

        grouped[shop].append((timestamp, filename, size))

    latest_two = {}

    for shop, files in grouped.items():
        files.sort(reverse=True)
        latest_two[shop] = files[:2]  # [newest, previous]

    return latest_two


# ======================
# INDEXING (FAST LOOKUPS)
# ======================
def build_filename_index(latest_two_map):
    """
    Builds fast lookup:
    filename -> files_for_shop
    """
    index = {}

    for shop, files in latest_two_map.items():
        for entry in files:
            filename = entry[1]
            index[filename] = files

    return index


# ======================
# PUBLIC PIPELINE API
# ======================
def get_two_latest_per_shop_from_bucket():
    """
    Pipeline entrypoint.
    """
    file_map = get_file_map()
    return get_two_latest_per_shop(file_map)


def get_filesize_change_percent(latest_filename, filename_index):
    """
    Calculates filesize percentage change between newest and previous file.

    Returns:
        float | None
    """
    files = filename_index.get(latest_filename)

    if not files or len(files) < 2:
        return None

    newest, previous = files[0], files[1]

    if newest[1] != latest_filename:
        return None

    newest_size = newest[2]
    previous_size = previous[2]

    if previous_size == 0:
        return None

    return abs(newest_size - previous_size) / previous_size * 100


# ======================
# DEBUG / CLI TOOL
# ======================
def print_shops_with_large_filesize_change(latest_two, threshold_percent, base_url):
    shop_counter = 0

    for shop, files in latest_two.items():

        if len(files) < 2:
            continue

        newest, previous = files

        newest_size = newest[2]
        previous_size = previous[2]

        if previous_size == 0:
            continue

        diff_percent = abs(newest_size - previous_size) / previous_size * 100

        if diff_percent > threshold_percent:

            shop_counter += 1

            print("=" * 40)
            print(f"{shop_counter}. Shop: {shop}")
            print("-" * 40)

            for idx, file in enumerate([previous, newest], start=1):

                filename = file[1]
                size = file[2]
                url = f"{base_url}{filename}"

                print(f"  {idx}) {filename} ({size} bytes)")
                print(f"     URL: {url}")

            print(f"Filesize verschil: {diff_percent:.2f}%")
            print("=" * 40 + "\n")

    print(f"Totaal shops met >{threshold_percent}% verschil: {shop_counter}")


# ======================
# MAIN (LOCAL DEBUG)
# ======================
def main():

    base_url = "https://pub-f75dabf2f86f4ad4ba4765ede21e47cc.r2.dev/"
    threshold_percent = 15

    latest_two = get_two_latest_per_shop_from_bucket()

    print(latest_two)

    print_shops_with_large_filesize_change(
        latest_two,
        threshold_percent,
        base_url
    )


if __name__ == "__main__":
    main()