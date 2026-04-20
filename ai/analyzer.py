import json
import logging

from openai import OpenAI

import config

logger = logging.getLogger(__name__)

_client = OpenAI(api_key=config.OPENAI_API_KEY)

PROMPT = """Compare two Dutch webshop homepage screenshots and identify NEW promotions.

Image 1: yesterday's homepage
Image 2: today's homepage

Report a promotion only if it is visible in Image 2 but NOT in Image 1, and it is a concrete, time-limited offer: a discount percentage, promo code, free gift, or deal.

Examples of promotions to REPORT:
- 20% korting op alles met code ELLE20
- Spring Sale! 15-50% korting op HEEL veel
- Cadeau: 3 parfum samples bij aankopen vanaf €60
- Koop 2, ontvang 2 gratis - geen code nodig, alleen 48 uur
- Tot 30% korting op kids fashion deals
- 25% korting op bestellingen vanaf €50 met code MOMENTEN25 t/m 23/03/2026
- 3e bh gratis voor leden
- Tot 60% korting op bijna alles met extra 10% korting met code MPDISKI

Examples of promotions to IGNORE:
- Gratis verzending vanaf €59
- Voor 20:00 besteld, morgen in huis
- 30 dagen gratis retourneren
- 10% korting bij inschrijving nieuwsbrief
- 10% korting voor nieuwe klanten met code HELLO
- Betaal achteraf met Klarna!
- Wekelijks nieuwe items online
- 15% studentenkorting
- Maak kans op een giftcard t.w.v. €100 bij inschrijving voor de nieuwsbrief

Respond with JSON only:
{
  "has_new_promotion": true or false,
  "promo_original": "exact visible text (max 25 words) or null",
  "promo_nl_summ": "brief dutch summary of promotion",
  "confidence": "high" | "medium" | "low"
}"""


def analyze_images(yesterday_url: str, today_url: str) -> dict:
    """
    Send both screenshot URLs to OpenAI for comparison.
    Returns dict with keys: has_new_promotion, promo_original, promo_nl_summ, confidence.
    """
    response = _client.chat.completions.create(
        model=config.OPENAI_MODEL,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": yesterday_url, "detail": "low"},
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": today_url, "detail": "low"},
                    },
                ],
            }
        ],
        max_tokens=200,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Could not parse OpenAI response as JSON: %s", raw)
        result = {"has_new_promotion": False, "promo_original": None, "promo_nl_summ": None, "confidence": "low"}

    logger.debug("OpenAI result: %s", result)
    return result
