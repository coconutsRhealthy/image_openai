from db.db_connection import get_database_connection

def get_all_webshop_ids_and_names():
    with get_database_connection() as connection:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT id, webshop_name FROM webshop_info ORDER BY webshop_name"
        cursor.execute(query)
        result = cursor.fetchall()

        cursor.close()
        return result  # Returns a list of dicts like [{'id': 1, 'webshop_name': 'Zalando'}, ...]

def get_screenshot_analysis_result_by_id(screenshot_id):
    with get_database_connection() as connection:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT analysis_result FROM screenshot_analysis WHERE id = %s"
        cursor.execute(query, (screenshot_id,))
        result = cursor.fetchone()
        cursor.close()

        if result:
            return result['analysis_result']
        else:
            return None

def get_screenshot_ids_since(datetime_from):
    with get_database_connection() as connection:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT id FROM screenshot_analysis WHERE screenshot_datetime >= %s ORDER BY screenshot_datetime"
        cursor.execute(query, (datetime_from,))
        results = cursor.fetchall()
        cursor.close()

        # Alleen de ID's teruggeven als een lijst
        return [row['id'] for row in results]

def get_previous_analysis_results(screenshot_id, num_previous):
    with get_database_connection() as connection:
        cursor = connection.cursor(dictionary=True)

        # 1️⃣ Eerst de webshop_id en screenshot_datetime van de huidige entry ophalen
        query_webshop = """
            SELECT webshop_id, screenshot_datetime 
            FROM screenshot_analysis 
            WHERE id = %s
        """
        cursor.execute(query_webshop, (screenshot_id,))
        current_entry = cursor.fetchone()
        if not current_entry or not current_entry['screenshot_datetime']:
            cursor.close()
            return {}  # geen entry gevonden of screenshot_datetime is NULL

        webshop_id = current_entry['webshop_id']
        screenshot_datetime = current_entry['screenshot_datetime']

        # 2️⃣ Vorige X entries ophalen van dezelfde webshop (voor de huidige datetime)
        query_previous = """
            SELECT screenshot_datetime, analysis_result 
            FROM screenshot_analysis
            WHERE webshop_id = %s
              AND screenshot_datetime < %s
            ORDER BY screenshot_datetime DESC
            LIMIT %s
        """
        cursor.execute(query_previous, (webshop_id, screenshot_datetime, num_previous))
        previous_entries = cursor.fetchall()
        cursor.close()

        # 3️⃣ Omzetten naar dict {datetime: analysis_result}, chronologisch (oudste eerst)
        result_dict = {row['screenshot_datetime']: row['analysis_result'] for row in reversed(previous_entries)}

        return result_dict

def get_webshop_id(screenshot_id):
    with get_database_connection() as connection:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT webshop_id FROM screenshot_analysis WHERE id = %s"
        cursor.execute(query, (screenshot_id,))
        result = cursor.fetchone()
        cursor.close()

    if result:
        return result['webshop_id']
    else:
        return None

def get_existing_screenshot_ids_in_detected_discounts() -> set:
    with get_database_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT screenshot_id FROM detected_discounts")
        rows = cursor.fetchall()
        cursor.close()
    return {row[0] for row in rows}


def main():
    screenshot_id = 292
    num_previous = 5
    previous_results = get_previous_analysis_results(screenshot_id, num_previous)

    if previous_results:
        for dt, analysis in previous_results.items():
            print(f"{dt}: {analysis}")
    else:
        print("Geen vorige entries gevonden.")

if __name__ == "__main__":
    main()
