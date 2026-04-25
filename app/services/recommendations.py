import os
from google import genai


def build_prompt(product, reviews, summary) -> str:
    product_name = getattr(product, "product_name", "Unknown product")
    category = getattr(product, "category", "Unknown category")
    brand = getattr(product, "brand", "Unknown brand")
    price = getattr(product, "price", "Unknown price")

    review_lines = []
    for r in reviews[:10]:
        source = getattr(r, "source", "unknown")
        rating = getattr(r, "rating", "unknown")
        text = getattr(r, "review_text", "")
        review_lines.append(f"- Source: {source}, Rating: {rating}, Review: {text}")

    avg_sentiment = getattr(summary, "avg_sentiment", None)
    top_complaints = getattr(summary, "top_complaints", []) or []
    top_praises = getattr(summary, "top_praises", []) or []

    complaints_text = ", ".join(top_complaints) if top_complaints else "None"
    praises_text = ", ".join(top_praises) if top_praises else "None"
    sentiment_text = str(avg_sentiment) if avg_sentiment is not None else "Unknown"

    return f"""
You are an AI marketing intelligence assistant for Magnetly.

Analyze this D2C home goods product and provide a concise business recommendation.

Product:
- Name: {product_name}
- Category: {category}
- Brand: {brand}
- Price: {price}

Current signals:
- Average sentiment: {sentiment_text}
- Top complaints: {complaints_text}
- Top praises: {praises_text}

Recent reviews:
{chr(10).join(review_lines) if review_lines else "No reviews available."}

Return your answer in exactly this format:

Recommendation:
<one short paragraph>

Investment Status:
<one of: promote, monitor, improve>

Marketing Focus:
<short phrase>

Improvement Priority:
<short phrase>
""".strip()


def generate_recommendation(prompt: str) -> str:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return (
            "Recommendation:\n"
            "Unable to generate a live AI recommendation because the Gemini API key is not configured.\n\n"
            "Investment Status:\n"
            "monitor\n\n"
            "Marketing Focus:\n"
            "Value and product clarity\n\n"
            "Improvement Priority:\n"
            "Configuration"
        )

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
        )
        text = response.text if response.text else ""
        if not text.strip():
            raise ValueError("Empty response from Gemini")
        return text
    except Exception as e:
        return (
            "Recommendation:\n"
            f"Recommendation generation failed: {str(e)}\n\n"
            "Investment Status:\n"
            "monitor\n\n"
            "Marketing Focus:\n"
            "Customer feedback review\n\n"
            "Improvement Priority:\n"
            "AI configuration"
        )


def parse_recommendation_sections(text: str) -> dict:
    result = {
        "recommendation": "",
        "investment_status": "monitor",
        "marketing_focus": "",
        "improvement_priority": "",
    }

    current_key = None
    key_map = {
        "recommendation:": "recommendation",
        "investment status:": "investment_status",
        "marketing focus:": "marketing_focus",
        "improvement priority:": "improvement_priority",
    }

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        lower = line.lower()
        if lower in key_map:
            current_key = key_map[lower]
            continue

        if current_key:
            if result[current_key]:
                result[current_key] += " " + line
            else:
                result[current_key] = line

    result["investment_status"] = result["investment_status"].strip().lower() or "monitor"
    if result["investment_status"] not in {"promote", "monitor", "improve"}:
        result["investment_status"] = "monitor"

    return result