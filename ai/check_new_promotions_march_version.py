import os
from openai import OpenAI

def check_new_promotions(screenshot_t_minus_1, screenshot_t):
    client = OpenAI(api_key="secret")
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

# Voorbeeld gebruik
print(check_new_promotions(
    "https://pub-f75dabf2f86f4ad4ba4765ede21e47cc.r2.dev/loavies_20260322_044956.jpg",
    "https://pub-f75dabf2f86f4ad4ba4765ede21e47cc.r2.dev/loavies_20260323_045022.jpg"
))