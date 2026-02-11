from db.db_connection import get_database_connection

def print_all_promotions_for_date(date_str):
    """
    Print all promotions for a specific date (YYYY-MM-DD),
    skipping any with 'no promotions found'.
    """
    query = """
        SELECT w.webshop_name, s.analysis_result, s.image_url, s.created_at
        FROM screenshot_analysis s
        JOIN webshop_info w ON s.webshop_id = w.id
        WHERE DATE(s.created_at) = %s
        ORDER BY w.webshop_name;
    """

    with get_database_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (date_str,))
        results = cursor.fetchall()
        cursor.close()

    # Filter results in Python
    filtered = [r for r in results if r['analysis_result'].strip().lower() != 'no promotions found']

    if not filtered:
        print(f"No promotions found for {date_str}.")
        return

    print(f"Promotions for {date_str}:\n" + "-" * 40)
    for row in filtered:
        print(f"{row['webshop_name']}")
        print(f"Promotion: {row['analysis_result']}")
        print()
        print(f"Image URL: {row['image_url']}")
        print(f"Added on: {row['created_at']}")
        print("-" * 40)

def print_new_promotions_for_date(date_str, show_analysis=False):
    """
    Print new promotions with both the current and previous screenshots
    for a specific date. Optionally print AI analysis results.
    """
    query = """
        SELECT 
            w.webshop_name,
            d.diff_summary,
            s_new.image_url AS new_image_url,
            s_new.analysis_result AS new_analysis,
            s_old.image_url AS old_image_url,
            s_old.analysis_result AS old_analysis,
            d.created_at
        FROM detected_discounts d
        JOIN webshop_info w ON d.webshop_id = w.id
        JOIN screenshot_analysis s_new ON d.screenshot_id = s_new.id
        LEFT JOIN screenshot_analysis s_old ON d.screenshot_prev_id = s_old.id
        WHERE DATE(d.created_at) = %s
        ORDER BY w.webshop_name;
    """

    with get_database_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (date_str,))
        results = cursor.fetchall()
        cursor.close()

    if not results:
        print(f"No new promotions detected for {date_str}.")
        return

    print(f"🆕 New Promotions Detected on {date_str}:\n" + "-" * 50)
    for row in results:
        print(f"🛒 {row['webshop_name']}")
        print(f"📝 Diff Summary: {row['diff_summary']}")
        print(f"➡️ Current Screenshot: {row['new_image_url']}")
        if show_analysis:
            print(f"   🧠 Current AI analysis: {row['new_analysis']}")

        print(f"⬅️ Previous Screenshot: {row['old_image_url'] or 'N/A'}")
        if show_analysis:
            print(f"   🧠 Previous AI analysis: {row['old_analysis'] or 'N/A'}")

        print(f"🕒 Detected at: {row['created_at']}")
        print("-" * 50)

if __name__ == "__main__":
    target_date = "2026-01-29"

    # Zonder extra AI-tekst
    # print_new_promotions_for_date(target_date)

    # Met extra AI-tekst
    print_new_promotions_for_date(target_date, show_analysis=True)