from openai import OpenAI

client = OpenAI(api_key='secret')

def extract_promotions_from_image(image_url):
    prompt_text = """
    You are an expert in e-commerce and online promotions.

Analyze the provided screenshot(s) of a Dutch webshop homepage and identify all clearly visible promotions, discounts, or special offers.

Return ONLY valid JSON in this format:

{
  "offers": [
    {
      "title": "Short neutral description",
      "title_dutch": "Dutch translation of title",
      "promotion_types": [
        "sitewide_hero_discount",
        "timed",
        "discount_code",
        "other"
      ],
      "original_promotion_text": "Exact visible text (max 25 words) or null",
      "position_on_page": "hero_banner | sidebar | footer | pop-up | other",
      "notes": "Extra visible details or null"
    }
  ]
}

Promotion types:
- sitewide_hero_discount: general discount on most/all products, prominent (e.g., hero banner)
- timed: time-limited promotion explicitly visible
- discount_code: requires entering a specific code
- other: any other visible offer (free shipping, gifts, bundles)

Rules:
1. Include only promotions explicitly visible.
2. Do NOT guess applicability, timing, or codes.
3. Multiple promotion_types allowed if explicitly supported.
4. Merge duplicates; include only the most prominent location.
5. Use null for missing or unclear fields.
6. If no promotions, return {"offers": []}.
    """

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[{
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt_text},
                {
                    "type": "input_image",
                    "image_url": image_url
                },
            ],
        }],
    )
    return response.output_text.strip()

# Test block
if __name__ == "__main__":
    # Local image file
    test_image_url = "zzz"

    result = extract_promotions_from_image(test_image_url)

    print(f"Analysis Result for Image: {test_image_url}")
    print(result)