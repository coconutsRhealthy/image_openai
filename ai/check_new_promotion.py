from openai import OpenAI
from db.db_connection import get_database_connection
from db.webshops_db_access import get_last_two_analysis_results_and_image_urls

client = OpenAI(api_key = 'secret')

def check_for_new_promotion(latest_description: str, previous_description: str) -> str:
    prompt_text = (
        "You are a marketing assistant helping to detect new promotions on webshop homepages.\n\n"
        "Compare the LATEST description with the PREVIOUS description.\n\n"
        "Important rules:\n"
        "- ONLY mention promotions that are **newly added** in the latest description.\n"
        "- DO NOT mention promotions that were removed or changed.\n"
        "- If there are no new promotions, reply with exactly: nothing new\n"
        "- If there are new promotions, describe them clearly in plain text.\n"
        "- If a discount code is mentioned, include it in the description.\n"
        "- Keep the output concise and free of introductions or summaries.\n\n"
        f"LATEST description:\n{latest_description}\n\n"
        f"PREVIOUS description:\n{previous_description}"
    )

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt_text}],
        temperature=0.2
    )

    return response.choices[0].message.content.strip()

if __name__ == "__main__":
    webshop = "asos"
    with get_database_connection() as connection:
        result = get_last_two_analysis_results_and_image_urls(connection, webshop)

    if result is None:
        print(f"Not enough data or no webshop found for '{webshop}'")
    else:
        latest, previous = result
        latest_result = latest['analysis_result']
        previous_result = previous['analysis_result']
        output = check_for_new_promotion(latest_result, previous_result)
        print("Change detected:" if output != "nothing new" else "No new promotions.")
        print(output)
