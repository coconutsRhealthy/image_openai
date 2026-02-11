import json
from datetime import datetime

from db.store_new_promotion_analysis import insert_novelty
from db.webshops_db_access import get_screenshot_ids_since, get_webshop_id, get_existing_screenshot_ids_in_detected_discounts
from util.json_util import create_openai_prompting_structure_current, create_openai_prompting_structure_previous
from ai.check_new_promotions_feb_version import analyze_promotion_novelty
from util.json_util import parse_openai_json


def write_analysis_to_db(webshop_id, screenshot_id, analysis_result_json: str):
    """
    Schrijf het resultaat naar DB.
    analysis_result_json moet een JSON-string zijn.
    """
    insert_novelty(webshop_id, screenshot_id, analysis_result_json)
    print(f"💾 [DB] Screenshot {screenshot_id} analysis result:")
    print(analysis_result_json)


def run_pipeline(datetime_from: datetime, num_previous=5):
    """
    Pipeline:
    1. Haal screenshot IDs op sinds datetime_from
    2. Filter IDs die al in detected_discounts staan
    3. Voor elke nieuwe screenshot:
        a) Huidige snapshot ophalen
        b) Vorige snapshots ophalen
        c) Analyse novelty uitvoeren
        d) Resultaat naar DB schrijven
    """
    screenshot_ids = get_screenshot_ids_since(datetime_from)
    print(f"ℹ️ Found {len(screenshot_ids)} screenshots since {datetime_from}")

    existing_ids = get_existing_screenshot_ids_in_detected_discounts()
    new_screenshot_ids = [sid for sid in screenshot_ids if sid not in existing_ids]
    print(f"ℹ️ {len(new_screenshot_ids)} screenshots are new (not yet in detected_discounts)")

    for screenshot_id in new_screenshot_ids:
        print(f"🔹 Processing screenshot_id: {screenshot_id}")

        # Bepaal webshop ID
        webshop_id = get_webshop_id(screenshot_id)

        # Huidige snapshot
        result_current = create_openai_prompting_structure_current(screenshot_id)

        # Vorige snapshots
        results_previous = create_openai_prompting_structure_previous(screenshot_id, num_previous)

        # Analyseer novelty
        novelty_result = analyze_promotion_novelty(result_current, results_previous)

        # JSON check
        parsed_novelty_result = parse_openai_json(novelty_result)
        if parsed_novelty_result is None:
            print("⚠️ Analysis result is invalid JSON")
            print("Original novelty_result:", novelty_result)
        else:
            # 🔒 Serialiseer naar JSON string
            parsed_novelty_json = json.dumps(parsed_novelty_result, ensure_ascii=False)

            # Schrijf naar DB
            write_analysis_to_db(webshop_id, screenshot_id, parsed_novelty_json)


if __name__ == "__main__":
    # Voorbeeld: alles sinds 1 februari 2026
    datetime_from = datetime(2026, 2, 4)
    run_pipeline(datetime_from=datetime_from, num_previous=5)
