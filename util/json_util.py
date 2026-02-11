# json_util.py
from ai.check_new_promotions_feb_version import analyze_promotion_novelty
from db.webshops_db_access import get_previous_analysis_results, get_screenshot_analysis_result_by_id
import json
from typing import Optional

def create_openai_prompting_structure_current(screenshot_id):
    current_result = get_screenshot_analysis_result_by_id(screenshot_id)
    parsed = parse_openai_json(current_result)
    return parsed

def create_openai_prompting_structure_previous(screenshot_id, num_previous):
    """
    Zet eerdere analyse-resultaten om naar een lijst van Python dicts
    die direct geschikt zijn als historische input voor analyze_promotion_novelty.
    """
    previous_results = get_previous_analysis_results(
        screenshot_id=screenshot_id,
        num_previous=num_previous
    )

    historical_list = []

    for screenshot_datetime, json_block in previous_results.items():
        parsed = parse_openai_json(json_block)



        historical_list.append({
            "date": screenshot_datetime.date().isoformat(),  # alleen datum, zoals je voorbeeld
            "offers": parsed.get("offers", [])
        })

    # Chronologisch (oudste eerst)
    historical_list.sort(key=lambda x: x["date"])

    return historical_list

def get_analysis_result_json(screenshot_id):
    result_json = get_screenshot_analysis_result_by_id(screenshot_id)
    parsed = parse_openai_json(result_json)
    return parsed

def get_offer(screenshot_id, offer_id):
    result_json = get_analysis_result_json(screenshot_id)

    if not result_json:
        return None

    offers = result_json.get("offers")
    if not isinstance(offers, list):
        return None

    for offer in offers:
        if offer.get("offer_id") == offer_id:
            return offer

    return None


def parse_openai_json(json_block: str) -> Optional[dict]:
    cleaned = json_block.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removesuffix("```").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        print(f"JSON kon niet geparsed worden:\n{cleaned}")
        return None


if __name__ == "__main__":
    # 🔧 Simpele handmatige test / debug entrypoint

    TEST_SCREENSHOT_ID = 446  # tijdelijk hardcoded
    NUM_PREVIOUS = 5

    results_previous = create_openai_prompting_structure_previous(
        screenshot_id=TEST_SCREENSHOT_ID,
        num_previous=NUM_PREVIOUS
    )

    result_current = create_openai_prompting_structure_current(
        screenshot_id=TEST_SCREENSHOT_ID
    )

    print("Test output:")
    # print(
    #     json.dumps(
    #         result_current,
    #         indent=2,
    #         ensure_ascii=False
    #     )
    # )

    print("******************")

    print(
        json.dumps(
            results_previous,
            indent=2,
            ensure_ascii=False
        )
    )

    # ai_result = analyze_promotion_novelty(result_current, results_previous)
    #
    # print(json.dumps(ai_result, indent=2, ensure_ascii=False))