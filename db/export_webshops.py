import json
from db_connection import get_database_connection


def export_webshops_to_json(output_file="sites.json"):
    query = """
        SELECT id, webshop_name, webshop_url
        FROM webshop_info
    """

    with get_database_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        rows = cursor.fetchall()

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    print(f"{len(rows)} webshops geëxporteerd naar {output_file}")


if __name__ == "__main__":
    export_webshops_to_json()
