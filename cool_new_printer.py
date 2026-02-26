import json
from datetime import date, datetime, timedelta
from pathlib import Path

from db.db_connection import get_database_connection
from run_pipeline_screenshot_analysis import make_image_url
from util.json_util import get_offer


BASE_SCREENSHOT_DIR = Path("/Users/lennartmac/Documents/ubuntu_mac_shared/screenshots")
JSON_OUTPUT_FILE = Path("/Users/lennartmac/Documents/test_wgk.json")

def resolve_screenshot_url(filename: str) -> str:
    return make_image_url(filename)

def get_all_offers_for_screenshot(screenshot_id: int) -> list:
    query = """
        SELECT analysis_result
        FROM screenshot_analysis
        WHERE id = %s
        LIMIT 1
    """

    with get_database_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (screenshot_id,))
        row = cursor.fetchone()
        cursor.close()

    if not row or not row[0]:
        return []

    try:
        parsed = json.loads(row[0])
    except Exception as e:
        print(f"⚠️ Could not parse analysis_result for screenshot {screenshot_id}: {e}")
        return []

    offers = parsed.get("offers")
    return offers if isinstance(offers, list) else []


def print_offers(label: str, offers: list):
    print(label)
    if not offers:
        print("   (no offers)")
        return

    for idx, offer in enumerate(offers, start=1):
        print(f"   {idx}.")
        print_offer_pretty(offer)
        print()  # lege regel tussen offers


def print_offer_pretty(offer: dict, indent: str = "   "):
    def line(label, value):
        print(f"{indent}  {label:<18}: {value}")

    print(f"{indent}- Offer")

    line("Title", offer.get("title", "-"))
    line("Type", offer.get("promotion_types", "-"))
    line("Position", offer.get("position_on_page", "-"))

    summary = offer.get("novelty_summary_nl")
    if summary:
        print(f"{indent}  Summary           : {summary}")


def shorten_text(text: str, max_words: int = 15) -> str:
    if not text:
        return "-"
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "…"


def print_new_offers_with_screenshot(
        for_date: date,
        show_previous_offers: bool = False,
        promotion_types_to_show: list = None
):
    start_dt = datetime.combine(for_date, datetime.min.time())
    end_dt = start_dt + timedelta(days=1)

    query = """
        SELECT
            d.id,
            d.webshop_id,
            w.webshop_name,
            w.webshop_url,
            d.screenshot_id,
            d.novelty_analysis,
            d.created_at                     AS detected_at,
            cur.image_filename               AS current_image_filename,
            cur.screenshot_datetime          AS current_screenshot_datetime,
            prev.image_filename              AS previous_image_filename,
            prev.screenshot_datetime         AS previous_screenshot_datetime,
            prev.id                          AS previous_screenshot_id
        FROM detected_discounts d
        JOIN webshop_info w
            ON w.id = d.webshop_id
        JOIN screenshot_analysis cur
            ON d.screenshot_id = cur.id
        LEFT JOIN screenshot_analysis prev
            ON prev.id = (
                SELECT p2.id
                FROM screenshot_analysis p2
                WHERE p2.webshop_id = cur.webshop_id
                  AND p2.screenshot_datetime < cur.screenshot_datetime
                ORDER BY p2.screenshot_datetime DESC
                LIMIT 1
            )
        WHERE d.created_at >= %s
          AND d.created_at < %s
        ORDER BY d.created_at DESC
    """

    with get_database_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (start_dt, end_dt))
        rows = cursor.fetchall()
        cursor.close()

    counter = 1
    json_entries = []  # hier verzamelen we alle offers voor JSON

    for row in rows:
        try:
            novelty_analysis = json.loads(row['novelty_analysis'])
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in novelty_analysis for screenshot {row['screenshot_id']}: {e}")
            continue

        offers = novelty_analysis.get("offers")
        if not isinstance(offers, list):
            continue

        new_offers = [
            offer for offer in offers
            if offer.get("is_new") is True and offer.get("offer_id")
        ]

        if not new_offers:
            continue

        # haal full offers op
        resolved_new_offers = []
        for novelty_offer in new_offers:
            offer_id = novelty_offer["offer_id"]
            full_offer = get_offer(row['screenshot_id'], offer_id)
            if full_offer:
                full_offer["novelty_summary_nl"] = novelty_offer.get("novelty_summary_nl")
                resolved_new_offers.append(full_offer)

        # filteren op promotion_types
        if promotion_types_to_show:
            filtered_offers = [
                offer for offer in resolved_new_offers
                if any(pt in promotion_types_to_show for pt in offer.get("promotion_types", []))
            ]
        else:
            filtered_offers = resolved_new_offers

        # Als er geen offers overblijven, print webshop niet
        if not filtered_offers:
            continue

        # Print webshop info
        print(f"{counter}.")
        print(
            f"🆕 {row['webshop_name']} | "
            f"Detected at {row['detected_at']} | "
            f"Screenshot ID {row['screenshot_id']}"
        )

        current_url = resolve_screenshot_url(row["current_image_filename"])
        print(f"🖼️ Current screenshot: {current_url} ({row['current_screenshot_datetime']})")

        print_offers("🆕 New offers (current):", filtered_offers)

        # Voeg offers toe aan JSON lijst
        for offer in filtered_offers:
            json_entries.append({
                "webshop_name": row['webshop_name'],
                "url": row.get("webshop_url", "-"),
                "korting_text": shorten_text(offer.get("original_promotion_text", "-")),
                "date": row['detected_at'].strftime("%Y-%m-%d %H:%M:%S") if row['detected_at'] else ""
            })

        if row.get("previous_screenshot_id"):
            prev_url = resolve_screenshot_url(row["previous_image_filename"])
            print(f"🕰️ Previous screenshot: {prev_url} ({row['previous_screenshot_datetime']})")

            if show_previous_offers:
                prev_offers = get_all_offers_for_screenshot(row["previous_screenshot_id"])
                if promotion_types_to_show:
                    prev_offers = [
                        offer for offer in prev_offers
                        if any(pt in promotion_types_to_show for pt in offer.get("promotion_types", []))
                    ]
                print_offers("📦 Offers (previous):", prev_offers)
        else:
            print("🕰️ Previous screenshot: (geen vorige screenshot)")

        print("-" * 60)
        counter += 1

    # # schrijf JSON bestand
    # if json_entries:
    #     with open(JSON_OUTPUT_FILE, "w", encoding="utf-8") as f:
    #         json.dump(json_entries, f, ensure_ascii=False, indent=2)
    #     print(f"✅ JSON file written to {JSON_OUTPUT_FILE}")

if __name__ == "__main__":
    # Voorbeeld: alleen sitewide_hero_discount en timed tonen
    print_new_offers_with_screenshot(
        date(2026, 2, 10),
        promotion_types_to_show=["sitewide_hero_discount", "timed", "discount_code"]
    )
