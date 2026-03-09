import boto3
from collections import defaultdict


def get_file_map(bucket_name, endpoint_url, access_key, secret_key):
    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )

    file_map = {}
    paginator = s3.get_paginator("list_objects_v2")

    for page in paginator.paginate(Bucket=bucket_name):
        for obj in page.get("Contents", []):
            file_map[obj["Key"]] = obj["Size"]

    return file_map


def get_two_latest_per_shop(file_map):
    grouped = defaultdict(list)

    for filename, size in file_map.items():
        parts = filename.rsplit("_", 2)  # laatste 2 delen = timestamp
        if len(parts) < 3:
            continue  # skip files die niet passen
        shop = parts[0]
        timestamp = parts[1] + parts[2].split(".")[0]

        grouped[shop].append((timestamp, filename, size))

    latest_two = {}
    for shop, files in grouped.items():
        files.sort(reverse=True)  # nieuwste eerst
        latest_two[shop] = files[:2]

    return latest_two


def print_shops_with_large_filesize_change(latest_two, threshold_percent, base_url):
    shop_counter = 0

    for shop, files in latest_two.items():
        if len(files) < 2:
            continue

        newest = files[0]
        previous = files[1]

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
            # Eerst oude file, dan nieuwe
            for idx, file in enumerate([previous, newest], start=1):
                filename = file[1]
                size = file[2]
                url = f"{base_url}{filename}"
                print(f"  {idx}) {filename} ({size} bytes)")
                print(f"     URL: {url}")
            print(f"Filesize verschil: {diff_percent:.2f}%")
            print("=" * 40 + "\n")

    print(f"Totaal shops met >{threshold_percent}% verschil: {shop_counter}")


def main():
    endpoint_url = "secret"
    access_key = "secret"
    secret_key = "secret"
    bucket_name = "screenshots"

    base_url = "https://pub-f75dabf2f86f4ad4ba4765ede21e47cc.r2.dev/"

    threshold_percent = 15  # inputparameter

    file_map = get_file_map(bucket_name, endpoint_url, access_key, secret_key)

    latest_two = get_two_latest_per_shop(file_map)

    print_shops_with_large_filesize_change(latest_two, threshold_percent, base_url)


if __name__ == "__main__":
    main()