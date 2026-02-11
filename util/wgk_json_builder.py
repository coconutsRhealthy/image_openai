import mysql.connector
import json
from datetime import datetime

# --- Configuratie ---
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "py_diski_webshops"
}

# --- Helper functies ---
def truncate_text(text, max_words=15):
    """Beperk tekst tot max_words woorden, eindig met ... als het langer is."""
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "…"

def get_offer_date(offer_id, novelty_json, fallback_datetime):
    if not novelty_json:
        return fallback_datetime

    offers = novelty_json.get("offers", [])
    for offer in offers:
        if offer.get("offer_id") == offer_id:
            dates = offer.get("seen_before_dates", [])
            if dates:
                # oudste datum pakken
                oldest = min(dates)
                return datetime.strptime(oldest, "%Y-%m-%d")

    return fallback_datetime

def fetch_promotions(target_date, promotion_types):
    """Haalt promoties op van een bepaalde datum met gewenste promotion_types."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    # Query alle screenshots van de target datum
    cursor.execute("""
        SELECT sa.id,
               sa.webshop_id,
               sa.analysis_result,
               sa.screenshot_datetime,
               wi.webshop_name,
               wi.webshop_url,
               dd.novelty_analysis
        FROM screenshot_analysis sa
        JOIN webshop_info wi ON sa.webshop_id = wi.id
        LEFT JOIN detected_discounts dd ON dd.screenshot_id = sa.id
        WHERE DATE(sa.screenshot_datetime) = %s
    """, (target_date,))

    results = cursor.fetchall()
    output_data = []

    for row in results:
        analysis_json = json.loads(row["analysis_result"])
        novelty_json = (
            json.loads(row["novelty_analysis"])
            if row["novelty_analysis"]
            else None
        )

        offers = analysis_json.get("offers", [])

        for offer in offers:
            # Filter op gewenste promotion_types
            if any(ptype in promotion_types for ptype in offer.get("promotion_types", [])):
                text = offer.get("title_dutch")
                offer_id = offer.get("offer_id")

                if not text or not offer_id:
                    continue

                offer_date = get_offer_date(
                    offer_id,
                    novelty_json,
                    row["screenshot_datetime"]
                )

                output_data.append({
                    "webshop_name": row["webshop_name"],
                    "url": row["webshop_url"],
                    "korting_text": truncate_text(text),
                    "date": offer_date.strftime("%Y-%m-%d %H:%M:%S")
                })

    cursor.close()
    conn.close()
    return output_data

def sort_by_date_desc(data):
    return sorted(
        data,
        key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d %H:%M:%S"),
        reverse=True
    )

def save_to_json(data, filename):
    """Slaat de data op in een JSON bestand."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- Main block ---
if __name__ == "__main__":
    TARGET_DATE = "2026-02-10"
    PROMOTION_TYPES = ["sitewide_hero_discount", "timed", "discount_code"]
    OUTPUT_JSON_FILE = "test_wgk22222.json"

    promotions = fetch_promotions(TARGET_DATE, PROMOTION_TYPES)

    # 🔽 sorteer van nieuw → oud
    promotions = sort_by_date_desc(promotions)

    save_to_json(promotions, OUTPUT_JSON_FILE)

    print(f"Succes! {len(promotions)} aanbiedingen weggeschreven naar {OUTPUT_JSON_FILE}.")
