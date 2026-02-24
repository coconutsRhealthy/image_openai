import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from db.db_connection import get_database_connection


def get_screenshots_for_day(start_dt: datetime, end_dt: datetime) -> List[Dict[str, Any]]:
    query = """
        SELECT
            sa.id,
            sa.webshop_id,
            w.webshop_name,
            sa.created_at,
            sa.analysis_result
        FROM screenshot_analysis sa
        JOIN webshop_info w
            ON w.id = sa.webshop_id
        WHERE sa.created_at >= %s
          AND sa.created_at < %s
        ORDER BY w.webshop_name, sa.created_at
    """

    with get_database_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (start_dt, end_dt))
        rows = cursor.fetchall()
        cursor.close()

    return rows


def print_offer_pretty(offer: dict, indent: str = "      "):
    def line(label, value):
        print(f"{indent}{label:<18}: {value}")

    print(f"{indent}- Offer")
    line("Title", offer.get("title", "-"))
    line("Type", offer.get("promotion_types", "-"))
    line("Position", offer.get("position_on_page", "-"))

    summary = offer.get("novelty_summary_nl")
    if summary:
        line("Summary", summary)


def print_offers(offers: list):
    for idx, offer in enumerate(offers, start=1):
        print(f"      {idx}.")
        print_offer_pretty(offer)
        print()


def offer_matches_promotion_filter(
        offer: dict,
        promotion_types_to_show: Optional[List[str]]
) -> bool:
    if not promotion_types_to_show:
        return True  # geen filter → alles tonen

    offer_types = offer.get("promotion_types", [])
    if not isinstance(offer_types, list):
        return False

    return any(pt in promotion_types_to_show for pt in offer_types)


def print_offers_for_created_at(
        for_datetime: datetime,
        promotion_types_to_show: Optional[List[str]] = None
):
    # Hele dag selecteren
    start_dt = datetime.combine(for_datetime.date(), datetime.min.time())
    end_dt = start_dt + timedelta(days=1)

    rows = get_screenshots_for_day(start_dt, end_dt)

    if not rows:
        print("Geen screenshots gevonden voor deze datum.")
        return

    current_webshop = None
    counter = 1
    printed_anything = False

    for row in rows:
        try:
            parsed = json.loads(row["analysis_result"]) if row["analysis_result"] else {}
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON for screenshot {row['id']}: {e}")
            continue

        offers = parsed.get("offers")
        if not isinstance(offers, list):
            continue

        # 🔥 Filter op promotion types
        filtered_offers = [
            offer for offer in offers
            if offer_matches_promotion_filter(offer, promotion_types_to_show)
        ]

        if not filtered_offers:
            continue  # skip screenshot zonder relevante offers

        printed_anything = True

        if row["webshop_name"] != current_webshop:
            if current_webshop is not None:
                print("-" * 60)

            print(f"{counter}. 🏪 {row['webshop_name']}")
            current_webshop = row["webshop_name"]
            counter += 1

        print(f"   Screenshot ID : {row['id']}")
        print(f"   Created at    : {row['created_at']}")
        print("   📦 Offers:")
        print_offers(filtered_offers)

    if printed_anything:
        print("-" * 60)
    else:
        print("Geen offers gevonden voor deze datum (met huidige filter).")


if __name__ == "__main__":
    print_offers_for_created_at(
        datetime(2026, 2, 14, 0, 0),
        promotion_types_to_show=[
            "sitewide_hero_discount",
            "timed",
            "discount_code",
            "other"
        ]
    )