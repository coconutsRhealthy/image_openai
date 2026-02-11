from openai import OpenAI
import json
import sys
from typing import Optional, Dict, Any


def analyze_new_offers(
        image_day_t: str,
        image_day_t_minus_1: str,
) -> Optional[Dict[str, Any]]:
    client = OpenAI(api_key = 'secret')

    prompt = """
Je krijgt twee screenshots van dezelfde webshop-homepage:
- Afbeelding 1: de huidige homepage
- Afbeelding 2: de homepage van de vorige dag

Taak:
- Vergelijk beide afbeeldingen en bepaal of er NIEUWE, site-brede aanbiedingen of campagnes zichtbaar zijn.

Output:
- Geef een JSON-object met EXACT twee velden per nieuwe aanbieding:
    {
      "aanbieding": "menselijke, hapklare tekst van de nieuwe aanbieding",
      "confidence": 0.0-1.0
    }
- Als er meerdere nieuwe aanbiedingen zijn, geef dan een lijst van deze JSON-objecten.
- Als er geen nieuwe aanbiedingen zijn, geef EXACT:
    {"aanbieding": "Geen nieuwe aanbiedingen gevonden", "confidence": 1.0}

Belangrijk:
- Houd de tekst van "aanbieding" direct geschikt om op een website te tonen.
- Geef geen extra uitleg of tekst buiten het JSON-formaat.
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": image_day_t},
                    {"type": "input_image", "image_url": image_day_t_minus_1},
                ],
            }
        ],
        max_output_tokens=500,
    )

    raw_output = response.output_text.strip()

    print("\n===== RAW OPENAI OUTPUT =====")
    print(raw_output)
    print("===== EINDE RAW OUTPUT =====\n")

    # Eventueel markdown fences strippen
    cleaned_output = (
        raw_output
        .removeprefix("```json")
        .removesuffix("```")
        .strip()
    )

    try:
        return json.loads(cleaned_output)

    except json.JSONDecodeError as e:
        print("❌ JSON parsing mislukt", file=sys.stderr)
        print(f"Foutmelding: {e}", file=sys.stderr)
        return None


def main():
    image_day_t = "https://raw.githubusercontent.com/wgknl/screenshots/main/esn/2026/01/29/esn_20260129_101010.png"
    image_day_t_minus_1 = "https://raw.githubusercontent.com/wgknl/screenshots/main/esn/2026/01/28/esn_20260128_110849.png"

    result = analyze_new_offers(
        image_day_t=image_day_t,
        image_day_t_minus_1=image_day_t_minus_1,
    )

    if result is None:
        print("⚠️ Analyse uitgevoerd, maar geen valide JSON ontvangen.")
        return

    print("✅ Analyse-resultaat (geparsed JSON):\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    if result.get("new_offers_detected"):
        print("\n🔥 Nieuwe aanbiedingen gedetecteerd!")
    else:
        print("\nℹ️ Geen nieuwe aanbiedingen gevonden.")


if __name__ == "__main__":
    main()
