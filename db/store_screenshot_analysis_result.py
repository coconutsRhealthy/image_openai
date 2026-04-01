from db.db_connection import get_database_connection
from datetime import datetime
import re

def get_webshop_id_by_name(webshop_name):
    with get_database_connection() as db_connection:
        cursor = db_connection.cursor()

        query = "SELECT id FROM webshop_info WHERE webshop_name = %s"
        cursor.execute(query, (webshop_name,))
        result = cursor.fetchone()

        cursor.close()
        return result[0] if result else None

def store_result(webshop_name, image_filename, analysis_result):
    webshop_id = get_webshop_id_by_name(webshop_name)
    if webshop_id is None:
        print(f"Webshop_name not found in webshop_info: {webshop_name}")
        return

    screenshot_dt = extract_datetime_from_image_filename(image_filename)
    if screenshot_dt is None:
        print(f"⚠️ Could not parse screenshot_datetime from image file: {image_filename}")
        screenshot_dt = None

    with get_database_connection() as db_connection:
        cursor = db_connection.cursor()

        insert_query = """
        INSERT INTO screenshot_analysis (webshop_id, image_filename, analysis_result, screenshot_datetime)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_query, (webshop_id, image_filename, analysis_result, screenshot_dt))
        db_connection.commit()

        cursor.close()
        print(f"Analysis stored for webshop_id={webshop_id}: {webshop_name} | datetime={screenshot_dt}")

def extract_datetime_from_image_filename(image_filename):
    match = re.search(
        r'_(\d{8})_(\d{6})\.(png|jpe?g)$',
        image_filename,
        re.IGNORECASE
    )
    if not match:
        return None

    date_part, time_part = match.group(1), match.group(2)
    return datetime.strptime(date_part + time_part, "%Y%m%d%H%M%S")

# Test block
if __name__ == "__main__":
    test_webshop_name = "zalando"
    test_image_filename = "zalando_20260202_103342"
    test_analysis_result = "This webshop offers a 20% discount on selected items."

    store_result(test_webshop_name, test_image_filename, test_analysis_result)
