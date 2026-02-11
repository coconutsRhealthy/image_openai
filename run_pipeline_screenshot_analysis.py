import json
import os
import uuid

from read_json_txt import read_txt_lines, create_url_screenshot_dict_from_txt
from ai.analyze_images import extract_promotions_from_image
from db.store_screenshot_analysis_result import store_result
from db.db_connection import get_database_connection
from util.json_util import parse_openai_json


def image_already_in_db(image_filename, connection):
    """Check of de image_url al in de database staat"""
    cursor = connection.cursor(dictionary=True)
    try:
        sql = "SELECT 1 FROM screenshot_analysis WHERE image_filename = %s LIMIT 1"
        cursor.execute(sql, (image_filename,))
        result = cursor.fetchone()
        return result is not None
    finally:
        cursor.close()

def main():
    txt_path = "/Users/lennartmac/Documents/Projects/image_openai/util/output_aaa_03.txt"
    lines = read_txt_lines(txt_path)
    url_screenshot_dict = create_url_screenshot_dict_from_txt(lines)

    with get_database_connection() as connection:
        for webshop_name, image_paths in url_screenshot_dict.items():
            for image_path in image_paths:
                image_filename = os.path.basename(image_path)

                if image_already_in_db(image_filename, connection):
                    print(f"Skipping {webshop_name}, image already in DB.")
                    continue

                print(f"Analyzing image for: {webshop_name}")
                try:
                    analysis_result = extract_promotions_from_image(image_path)
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

                except Exception as e:
                    print(f"Failed for {webshop_name}: {e}")

if __name__ == "__main__":
    main()
