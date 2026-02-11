# main.py
import json
from datetime import date
from db.webshops_db_access import get_screenshot_ids_since
from util.json_util import get_analysis_result_json


def print_all_analysis_results_since():
    start_date = date(2026, 1, 1)
    screenshot_ids = get_screenshot_ids_since(start_date)

    for screenshot_id in screenshot_ids:
        result_json = get_analysis_result_json(screenshot_id)

        if result_json:
            try:
                print(json.dumps(result_json, indent=4))
            except json.JSONDecodeError:
                print("Het resultaat is geen geldige JSON:")
                print(result_json)
        else:
            print(f"Geen resultaat gevonden voor screenshot_id {screenshot_id}")

if __name__ == "__main__":
    print_all_analysis_results_since()
