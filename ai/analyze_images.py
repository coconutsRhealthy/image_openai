from openai import OpenAI
import base64

client = OpenAI(api_key='secret')

def extract_promotions_from_image(image_path):
    # Read image and convert to base64
    with open(image_path, "rb") as f:
        image_base64 = base64.b64encode(f.read()).decode("utf-8")

    prompt_text = """
    You are an expert in e-commerce and online promotions.

Analyze the provided screenshot of a Dutch webshop homepage.
Identify all promotions, discounts, or special offers that are clearly visible.

Return ONLY valid JSON in the exact format below.

{
  "offers": [
    {
      "title": "Short, clear description of the promotion",
      "title_dutch": "Translation of title in Dutch",
      "promotion_types": [
        "sitewide_hero_discount",
        "timed",
        "discount_code",
        "other"
      ],
      "original_promotion_text": "Exact visible text from the website or null",
      "position_on_page": "hero_banner | sidebar | footer | pop-up | other",
      "notes": "Extra visible details or null"
    }
  ]
}

Promotion type definitions:
- sitewide_hero_discount: A general discount that applies to most or all products and is prominently displayed (e.g. a main hero banner).
- timed: A promotion that is explicitly time-limited, with a clear visible time indication such as an end date, countdown, or phrases like 'today only', 'this weekend', or 'ends tonight'.
- discount_code: A promotion that requires entering a specific discount code.
- other: Any promotion that does not fit the above categories (e.g. free shipping, gifts, bundles).

Rules:
1. Only include promotions that are explicitly visible in the screenshot.
2. Do NOT guess or infer discounts, time limits, sitewide applicability, or code usage.
3. Multiple promotion_types may apply to a single promotion.
4. Only include a promotion_type if it is clearly and explicitly supported by visible text.
5. The "original_promotion_text" must exactly match the visible text on the website, but it should **not exceed 25 words**. 
6. The "title" should be a short neutral summary and must NOT include information that is not explicitly visible.
7. Use null for missing or unclear information.
8. Use the most prominent visible location as "position_on_page".
9. **Do NOT include the same promotion more than once. If two promotions have the same meaning but slightly different wording, only include one of them. Merge duplicates if necessary.**
10. After identifying promotions, perform a final check to remove any near-duplicates that convey the same offer, even if wording differs.
11. Do NOT include explanations or commentary outside the JSON.
12. If no promotions are visible, return an empty offers array.
    """

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[{
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt_text},
                {
                    "type": "input_image",
                    "image_url": f"data:image/png;base64,{image_base64}"
                },
            ],
        }],
    )
    return response.output_text.strip()

# Test block
if __name__ == "__main__":
    # Local image file
    test_image_path = "/Users/lennartmac/Documents/ubuntu_mac_shared/screenshots/zalando/2026/02/02/zalando_20260202_103342.png"

    result = extract_promotions_from_image(test_image_path)

    print(f"Analysis Result for Image: {test_image_path}")
    print(result)