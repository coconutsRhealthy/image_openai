import json
from openai import OpenAI

client = OpenAI(api_key = 'secret')


def analyze_promotion_novelty(latest_promotions: dict, historical_promotions: list):
    prompt_text = """
You are a data analyst specialized in e-commerce promotions.

Your task:
Compare a list of current promotions with a list of historical promotions
and determine which current promotions are new.

Important rules:
- Compare promotions by semantic meaning, not exact wording
- Ignore differences in capitalization, punctuation, phrasing, or notes
- A promotion is NOT new if a very similar promotion
  (same discount value and same intent or scope) existed before
- Only use the historical data provided
- Do NOT infer or invent dates or promotions
- If no matching historical promotion exists, the promotion is new

Additional task (only for new promotions):
- For each offer where is_new = true, generate a short Dutch sentence
  explaining:
  1. Why the promotion is new compared to historical promotions
  2. What the offer or discount is
  3. What makes it attractive for the consumer

Rules for the Dutch sentence:
- Write exactly ONE sentence in Dutch
- Be factual and concise
- Maximum length: 25 words
- Base the explanation ONLY on the provided promotion text
- Do NOT invent benefits, urgency, or conditions
- Do NOT use marketing exaggerations
- If the promotion is NOT new, return an empty string for this field

Output rules:
- Respond with VALID JSON only
- Follow the output schema exactly
- Do not include explanations or commentary
"""

    user_payload = {
        "latest_promotions": latest_promotions,
        "historical_promotions": historical_promotions,
        "output_schema": {
            "offers": [
                {
                    "offer_id": "uuid",
                    "is_new": "boolean",
                    "seen_before_dates": [],
                    "seen_before_offer_ids": [],
                    "novelty_summary_nl": "string"
                }
            ]
        }
    }

    response = client.responses.create(
        model="gpt-4.1",
        input=[
            {
                "role": "system",
                "content": prompt_text.strip()
            },
            {
                "role": "user",
                "content": json.dumps(user_payload, ensure_ascii=False)
            }
        ],
        temperature=0
    )

    return response.output_text.strip()


# -------------------------------
# Example usage / test block
# -------------------------------
if __name__ == "__main__":

    latest = {
        "shop": "zalando",
        "analysis_date": "2026-02-02",
        "offers": [
            {
                "title": "15% EXTRA korting op beauty items en meer",
                "value": "15%",
                "promotion_type": "percentage",
                "scope": "category"
            }
        ]
    }

    historical = [
        {
            "date": "2026-02-01",
            "offers": [
                {
                    "title": "15% EXTRA korting op beauty items en meer",
                    "value": "15%"
                }
            ]
        },
        {
            "date": "2026-01-30",
            "offers": [
                {
                    "title": "Tot 50% korting op je favoriete merken",
                    "value": "50%"
                }
            ]
        }
    ]

    result = analyze_promotion_novelty(latest, historical)

    print(json.dumps(result, indent=2, ensure_ascii=False))
