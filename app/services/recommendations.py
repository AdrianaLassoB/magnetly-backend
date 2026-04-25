from google import genai

from app.config import get_settings

settings = get_settings()


def build_prompt(product_name: str, category: str | None, avg_sentiment: float | None,
                 positive_count: int, negative_count: int,
                 top_complaints: list[str] | None, top_praises: list[str] | None,
                 estimated_revenue: float | None) -> str:
    return f"""
You are generating a concise recommendation for Magnetly, an AI marketing intelligence platform for fast growing D2C home goods brands.

Product: {product_name}
Category: {category}
Average sentiment: {avg_sentiment}
Positive reviews: {positive_count}
Negative reviews: {negative_count}
Estimated revenue: {estimated_revenue}
Top complaints: {top_complaints}
Top praises: {top_praises}

Return exactly 3 short lines in this format:
Recommended action: promote, improve, or monitor
Why: one sentence for a marketing or product lead
Marketing focus: one sentence on the message or improvement to prioritize
""".strip()


def parse_recommendation_sections(text: str) -> tuple[str, str | None, str | None]:
    recommendation = text.strip()
    why = None
    marketing_focus = None
    for line in text.splitlines():
        clean = line.strip()
        lower = clean.lower()
        if lower.startswith('why:'):
            why = clean[4:].strip()
        elif lower.startswith('marketing focus:'):
            marketing_focus = clean[len('marketing focus:'):].strip()
    return recommendation, why, marketing_focus


def generate_recommendation(prompt: str) -> str:
    if not settings.google_api_key:
        return 'Recommended action: monitor\nWhy: Gemini API key is not configured yet.\nMarketing focus: verify your environment settings and then regenerate.'

    client = genai.Client(api_key=settings.google_api_key)
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
    return response.text.strip() if response.text else 'Recommended action: monitor\nWhy: No recommendation returned.\nMarketing focus: review the input data and retry.'
