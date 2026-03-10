import boto3
import json
from datetime import date, datetime, timedelta
from pathlib import Path
import os

from db.db_connection import get_database_connection
from run_pipeline_screenshot_analysis import make_image_url
from util.json_util import get_offer
from zoneinfo import ZoneInfo


BASE_SCREENSHOT_DIR = Path("/Users/lennartmac/Documents/ubuntu_mac_shared/screenshots")


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
    except Exception:
        return []

    offers = parsed.get("offers")
    return offers if isinstance(offers, list) else []


def offer_to_html(offer: dict) -> str:
    title = offer.get("title", "-")
    types = ", ".join(offer.get("promotion_types", []))
    position = offer.get("position_on_page", "-")
    summary = offer.get("novelty_summary_nl")

    html = f"""
    <div class="offer">
        <div class="offer-title">{title}</div>
        <div class="offer-meta">
            <span class="badge">{types}</span>
            <span class="position">{position}</span>
        </div>
    """

    if summary:
        html += f"""
        <div class="summary">
            {summary}
        </div>
        """

    html += "</div>"

    return html


def offers_block_html(label: str, offers: list) -> str:

    html = f'<div class="offers-block"><h3>{label}</h3>'

    if not offers:
        html += "<div class='no-offers'>No offers</div>"
    else:
        for offer in offers:
            html += offer_to_html(offer)

    html += "</div>"

    return html


def print_new_offers_with_screenshot(
        for_date: date,
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

    html_parts = []

    html_parts.append("""
<html>
<head>
<meta charset="utf-8">
<style>

body{
    font-family: Arial, sans-serif;
    background:#f5f5f5;
    padding:30px;
}

.shop{
    background:white;
    border-radius:8px;
    padding:20px;
    margin-bottom:30px;
    box-shadow:0 2px 6px rgba(0,0,0,0.1);
}

.shop h2{
    margin-top:0;
}

.screenshots{
    display:flex;
    gap:20px;
    margin-bottom:20px;
}

.screenshot img{
    max-width:350px;
    border-radius:6px;
}

.offer{
    padding:10px;
    border-bottom:1px solid #eee;
}

.offer-title{
    font-weight:bold;
}

.badge{
    background:#eee;
    padding:2px 6px;
    border-radius:4px;
    margin-right:6px;
}

.summary{
    color:#444;
    margin-top:4px;
}

</style>
</head>
<body>
<h1>Detected Offers</h1>
""")

    for row in rows:

        try:
            novelty_analysis = json.loads(row['novelty_analysis'])
        except:
            continue

        offers = novelty_analysis.get("offers")
        if not isinstance(offers, list):
            continue

        new_offers = [
            offer for offer in offers
            if offer.get("is_new") is True and offer.get("offer_id")
        ]

        resolved_new_offers = []

        for novelty_offer in new_offers:

            offer_id = novelty_offer["offer_id"]

            full_offer = get_offer(row['screenshot_id'], offer_id)

            if full_offer:
                full_offer["novelty_summary_nl"] = novelty_offer.get("novelty_summary_nl")
                resolved_new_offers.append(full_offer)

        if promotion_types_to_show:
            resolved_new_offers = [
                offer for offer in resolved_new_offers
                if any(pt in promotion_types_to_show for pt in offer.get("promotion_types", []))
            ]

        if not resolved_new_offers:
            continue

        current_url = resolve_screenshot_url(row["current_image_filename"])

        html_parts.append(f"""
<div class="shop">

<h2>🆕 {row['webshop_name']}</h2>

<div>
Detected at: {row['detected_at']}<br>
Screenshot ID: {row['screenshot_id']}
</div>

<div class="screenshots">

<div class="screenshot">
<a href="{current_url}" target="_blank">
<img src="{current_url}">
</a>
<div>{row['current_screenshot_datetime']}</div>
</div>
""")

        if row.get("previous_screenshot_id"):

            prev_url = resolve_screenshot_url(row["previous_image_filename"])

            html_parts.append(f"""
<div class="screenshot">
<a href="{prev_url}" target="_blank">
<img src="{prev_url}">
</a>
<div>{row['previous_screenshot_datetime']}</div>
</div>
""")

        html_parts.append("</div>")

        html_parts.append(
            offers_block_html("🆕 New offers", resolved_new_offers)
        )

        html_parts.append("</div>")

    html_parts.append("</body></html>")

    final_html = "\n".join(html_parts)

    filename = for_date.strftime("%Y-%m-%d.html")

    r2_acc_id = os.getenv("R2_ACCOUNT_ID")
    r2_access_key = os.getenv("R2_ACCESS_KEY")
    r2_secret_key = os.getenv("R2_SECRET_KEY")
    r2_endpoint = f"https://{r2_acc_id}.r2.cloudflarestorage.com"

    r2 = boto3.client(
        "s3",
        endpoint_url=r2_endpoint,
        aws_access_key_id=r2_access_key,
        aws_secret_access_key=r2_secret_key,
    )

    r2.put_object(
        Bucket="promotions",
        Key=filename,
        Body=final_html.encode("utf-8"),
        ContentType="text/html",
    )

    print("html geupload naar r2! :)")


if __name__ == "__main__":

    yesterday_amsterdam = datetime.now(ZoneInfo("Europe/Amsterdam")).date() - timedelta(days=1)

    print_new_offers_with_screenshot(
        yesterday_amsterdam,
        promotion_types_to_show=["sitewide_hero_discount", "timed", "discount_code"]
    )