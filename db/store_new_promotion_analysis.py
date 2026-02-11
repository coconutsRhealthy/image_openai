from db.db_connection import get_database_connection
from datetime import datetime
import json

def insert_detected_discounts(entries):
    with get_database_connection() as conn:
        cursor = conn.cursor()

        screenshot_query = """
            SELECT id FROM screenshot_analysis
            WHERE webshop_id = %s
            ORDER BY created_at DESC
            LIMIT 2
        """

        insert_query = """
            INSERT INTO detected_discounts (webshop_id, screenshot_id, screenshot_prev_id, diff_summary, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """

        for entry in entries:
            webshop_id = entry['webshop_id']
            diff_summary = entry['diff_summary']

            cursor.execute(screenshot_query, (webshop_id,))
            screenshots = cursor.fetchall()

            if not screenshots:
                print(f"No screenshots found for webshop_id {webshop_id}. Skipping.")
                continue

            screenshot_id = screenshots[0][0]
            screenshot_prev_id = screenshots[1][0] if len(screenshots) > 1 else None

            cursor.execute(insert_query, (
                webshop_id,
                screenshot_id,
                screenshot_prev_id,
                diff_summary,
                datetime.now()
            ))

        conn.commit()
        print("All valid entries inserted.")
        cursor.close()


def insert_novelty(webshop_id: int, screenshot_id: int, analysis_result: str):
    query = """
        INSERT INTO detected_discounts (webshop_id, screenshot_id, novelty_analysis)
        VALUES (%s, %s, %s)
    """

    with get_database_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (webshop_id, screenshot_id, analysis_result))
        conn.commit()
        cursor.close()

    print(f"💾 [DB] Inserted novelty analysis for screenshot {screenshot_id}")



# Example usage
if __name__ == "__main__":
    entries = [
        {"webshop_id": 5, "diff_summary": "New discount detected on homepage"},
        {"webshop_id": 8, "diff_summary": "Flash sale started"},
    ]

    insert_detected_discounts(entries)
