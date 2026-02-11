from db.db_connection import get_database_connection
from db.webshops_db_access import get_all_webshop_ids_and_names, get_last_two_analysis_results_and_image_urls
from db.store_new_promotion_analysis import insert_detected_discounts
from ai.check_new_promotion import check_for_new_promotion


def run_pipeline():
    entries_to_insert = []

    webshops = get_all_webshop_ids_and_names()

    with get_database_connection() as connection:
        for webshop in webshops:
            webshop_id = webshop["id"]
            webshop_name = webshop["webshop_name"]

            result = get_last_two_analysis_results_and_image_urls(connection, webshop_name)
            if result is None:
                print(f"[{webshop_name}] Not enough data.")
                continue

            latest, previous = result
            latest_result = latest["analysis_result"]
            previous_result = previous["analysis_result"]

            diff_summary = check_for_new_promotion(latest_result, previous_result)

            if diff_summary.lower() == "nothing new":
                print(f"[{webshop_name}] No new promotions.")
                continue

            print(f"[{webshop_name}] New promotion: {diff_summary}")
            entries_to_insert.append({
                "webshop_id": webshop_id,
                "diff_summary": diff_summary
            })

    if entries_to_insert:
        insert_detected_discounts(entries_to_insert)
    else:
        print("No new promotions found for any webshops.")

if __name__ == "__main__":
    run_pipeline()
