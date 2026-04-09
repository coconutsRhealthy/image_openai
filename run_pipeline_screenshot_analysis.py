import json
import uuid

from ai.analyze_images import extract_promotions_from_image
from db.store_screenshot_analysis_result import store_result
from db.db_connection import get_database_connection
from util.json_util import parse_openai_json
from util.r2_image_utils import (
    get_files_with_metadata_per_shop,
    get_two_latest_files_per_shop,
    build_filename_index,
    calculate_filesize_change_percent
)

BASE_URL = "https://pub-f75dabf2f86f4ad4ba4765ede21e47cc.r2.dev"
FILESIZE_THRESHOLD = 15

def get_existing_images(connection):
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT image_filename FROM screenshot_analysis")
        rows = cursor.fetchall()
    finally:
        cursor.close()
    return {row["image_filename"] for row in rows}

def make_image_url(image_filename: str) -> str:
    return f"{BASE_URL}/{image_filename}"

def main():
    files_per_shop = get_files_with_metadata_per_shop()
    latest_two = get_two_latest_files_per_shop(files_per_shop)
    filename_index = build_filename_index(latest_two)

    with get_database_connection() as connection:
        existing_images = get_existing_images(connection)
        print(f"ℹ️ {len(existing_images)} images already stored in DB")

        for shop, files in files_per_shop.items():
            for _, filename, filesize in files:

                if filename in existing_images:
                    continue

                print(f"Analyzing image for: {shop}")
                try:
                    image_url = make_image_url(filename)
                    change_percent = calculate_filesize_change_percent(filename, filename_index)

                    if change_percent is None or change_percent < FILESIZE_THRESHOLD:
                        analysis_result = json.dumps({"offers": []}, ensure_ascii=False)
                    else:
                        analysis_result = extract_promotions_from_image(image_url)

                    parsed_result = parse_openai_json(analysis_result) or {}
                    if "offers" in parsed_result and isinstance(parsed_result["offers"], list):
                        for offer in parsed_result["offers"]:
                            offer["offer_id"] = str(uuid.uuid4())

                    store_result(shop, filename, json.dumps(parsed_result, ensure_ascii=False), filesize)
                    existing_images.add(filename)

                except Exception as e:
                    print(f"Failed for {shop}: {e}")

if __name__ == "__main__":
    main()