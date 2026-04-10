import json
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def analyze_promotion_novelty(latest_promotions: dict, historical_promotions: list):
    prompt_text = """
You are a data analyst specialized in e-commerce promotions.

Your task:
Compare a list of current promotions with a list of historical promotions
and determine which current promotions are NEW.

Novelty rules:
- Compare by semantic meaning, not exact wording
- Ignore differences in capitalization, punctuation, or minor phrasing
- A promotion is NOT new if a semantically similar promotion existed within the last 14 days
  (same type of discount and same scope — e.g. "20% off sitewide" = "20% korting op alles")
- A different discount value on the same scope DOES count as new (e.g. 20% → 30% sitewide)
- Only use the historical data provided — do not invent or assume dates
- If no matching historical promotion exists, the promotion is new

For each offer where is_new = true, write a short Dutch sentence:
- Exactly ONE sentence in Dutch
- Maximum 25 words
- Describe what the offer is
- Be factual — do NOT invent urgency, conditions, or marketing language
- If is_new = false, return an empty string

Output rules:
- Respond with VALID JSON only
- Follow the output schema exactly
- Do not include explanations or commentary outside the JSON
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
