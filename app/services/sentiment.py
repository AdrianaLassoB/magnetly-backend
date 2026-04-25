from functools import lru_cache
import re

MODEL_NAME = "distilbert/distilbert-base-uncased-finetuned-sst-2-english"


@lru_cache(maxsize=1)
def get_sentiment_pipeline():
    from transformers import pipeline
    return pipeline("sentiment-analysis", model=MODEL_NAME)


def analyze_sentiment(text: str) -> dict:
    classifier = get_sentiment_pipeline()
    result = classifier(text)[0]
    return {
        "label": result["label"],
        "score": float(result["score"]),
    }


def classify_sentiment(text: str) -> str:
    result = analyze_sentiment(text)
    return result["label"].lower()


def extract_keywords(text: str) -> list[str]:
    words = re.findall(r"\b[a-zA-Z][a-zA-Z]+\b", text.lower())
    stopwords = {
        "the", "and", "for", "with", "this", "that", "have", "from", "were",
        "been", "they", "their", "about", "would", "there", "which", "arrived",
        "because", "very", "just", "into", "really", "nice", "great"
    }
    filtered = [w for w in words if w not in stopwords and len(w) > 3]
    seen = []
    for word in filtered:
        if word not in seen:
            seen.append(word)
    return seen[:8]


def infer_theme(text: str) -> str:
    lowered = text.lower()

    theme_keywords = {
        "shipping": ["shipping", "delivery", "arrived", "late", "damaged", "package", "packaging"],
        "quality": ["quality", "broken", "leaks", "defect", "durable", "cheap", "weak"],
        "design": ["design", "beautiful", "style", "color", "aesthetic", "look"],
        "comfort": ["soft", "comfortable", "texture", "cozy"],
        "price": ["price", "expensive", "cheap", "value", "worth"],
        "usability": ["easy", "difficult", "lid", "instructions", "use", "carry"],
    }

    for theme, keywords in theme_keywords.items():
        if any(keyword in lowered for keyword in keywords):
            return theme

    return "general"


def fallback_investment_status(avg_sentiment: float | None, theme: str | None = None) -> str:
    if avg_sentiment is None:
        return "monitor"

    if avg_sentiment >= 0.75:
        return "promote"

    if avg_sentiment >= 0.5:
        if theme in {"shipping", "quality", "usability"}:
            return "monitor"
        return "promote"

    return "improve"
