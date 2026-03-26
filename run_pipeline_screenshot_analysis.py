import json
import uuid

from ai.analyze_images import extract_promotions_from_image
from db.store_screenshot_analysis_result import store_result
from db.db_connection import get_database_connection
from util.images_on_r2 import get_filenames_on_r2_per_webshop
from util.json_util import parse_openai_json

from util.r2_image_sizes import (
    get_two_latest_per_shop_from_bucket,
    build_filename_index,
    get_filesize_change_percent
)


def get_existing_images(connection):
    """
    Haal alle bestaande image_filenames op uit screenshot_analysis.
    Returnt een set voor snelle lookup.
    """
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("SELECT image_filename FROM screenshot_analysis")
        rows = cursor.fetchall()
    finally:
        cursor.close()

    return {row["image_filename"] for row in rows}

def make_image_url(image_filename: str) -> str:
    base_url = "https://pub-f75dabf2f86f4ad4ba4765ede21e47cc.r2.dev"
    return f"{base_url}/{image_filename}"

def main():

    filesize_threshold = 15

    filename_screenshot_dict = get_filenames_on_r2_per_webshop()

    # 🔹 Filesize index bouwen
    latest_two = get_two_latest_per_shop_from_bucket()
    filename_index = build_filename_index(latest_two)

    with get_database_connection() as connection:
        # 🔹 Eén keer alle bestaande images ophalen
        existing_images = get_existing_images(connection)
        print(f"ℹ️ {len(existing_images)} images already stored in DB")

        for webshop_name, image_filenames in filename_screenshot_dict.items():
            for image_filename in image_filenames:

                # 🔹 Skip als image al in DB zit
                if image_filename in existing_images:
                    # print(f"Skipping {image_filename}, already in DB.")
                    continue

                # 🔹 Filesize change check
                percent_filesize_change = get_filesize_change_percent(
                    image_filename,
                    filename_index
                )

                if percent_filesize_change is None:
                    continue

                if percent_filesize_change < filesize_threshold:
                    continue

                print(f"Analyzing image for: {webshop_name}")
                try:
                    image_url = make_image_url(image_filename)
                    analysis_result = "{}"
                    print(f"Analysis result: {analysis_result}")

                    parsed_result = parse_openai_json(analysis_result)
                    if parsed_result is None:
                        print("Analysis result is invalid JSON, storing empty object instead.")
                        parsed_result = {}

                    # Voeg 'offer_id' toe aan elke entry in 'offers', als die key bestaat
                    if "offers" in parsed_result and isinstance(parsed_result["offers"], list):
                        for offer in parsed_result["offers"]:
                            offer["offer_id"] = str(uuid.uuid4())

                    parsed_result_json = json.dumps(parsed_result, ensure_ascii=False)

                    # Store result in DB using foreign key logic
                    store_result(webshop_name, image_filename, parsed_result_json)

                    # 🔹 Update cache zodat dezelfde image niet opnieuw verwerkt wordt
                    existing_images.add(image_filename)

                except Exception as e:
                    print(f"Failed for {webshop_name}: {e}")

if __name__ == "__main__":
    main()
