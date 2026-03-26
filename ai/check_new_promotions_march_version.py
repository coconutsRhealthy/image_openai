import os
import json
from openai import OpenAI

def check_new_promotions(screenshot_t_minus_1, screenshot_t):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = ("Je krijgt twee screenshots van een webshop. De eerste is van tijdstip t-1, de tweede van tijdstip t. "
              "Vermeld kort nieuwe promoties en aanbiedingen (maximaal 1 regel). Indien niets nieuws antwoord met: '-'")

    resp = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": screenshot_t_minus_1}},
                {"type": "image_url", "image_url": {"url": screenshot_t}}
            ]
        }]
    )
    return resp.choices[0].message.content

def check_new_promotions_json(screenshot_t_minus_1, screenshot_t):
    result = check_new_promotions(screenshot_t_minus_1, screenshot_t)

    if result.strip() == "-":
        # lege JSON teruggeven
        return json.dumps({"offers": []}, ensure_ascii=False)

    # anders JSON-formaat zoals gevraagd
    offer_entry = {
        "offer_id": "",
        "is_new": True,
        "seen_before_dates": [],
        "seen_before_offer_ids": [],
        "novelty_summary_nl": result.strip()
    }

    return json.dumps({"offers": [offer_entry]}, ensure_ascii=False)

# Voorbeeld gebruik
screenshot1 = "https://pub-f75dabf2f86f4ad4ba4765ede21e47cc.r2.dev/loavies_20260322_044956.jpg"
screenshot2 = "https://pub-f75dabf2f86f4ad4ba4765ede21e47cc.r2.dev/loavies_20260323_045022.jpg"

json_output = check_new_promotions_json(screenshot1, screenshot2)
print(json_output)