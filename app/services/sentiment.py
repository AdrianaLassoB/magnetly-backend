from collections import Counter
import re
from functools import lru_cache

from transformers import pipeline

from app.config import get_settings

settings = get_settings()

THEME_KEYWORDS = {
    'shipping': ['shipping', 'delivery', 'late', 'package', 'packaging', 'arrived'],
    'quality': ['quality', 'broken', 'cheap', 'durable', 'material', 'sturdy'],
    'price': ['price', 'expensive', 'cheap', 'value', 'worth'],
    'design': ['design', 'style', 'beautiful', 'look', 'color'],
    'accessibility': ['accessibility', 'easy', 'difficult', 'instructions', 'usable'],
    'support': ['support', 'service', 'help', 'refund', 'return'],
}

POSITIVE_HINTS = {'love', 'great', 'beautiful', 'perfect', 'excellent', 'amazing', 'durable'}
NEGATIVE_HINTS = {'broken', 'late', 'bad', 'terrible', 'poor', 'cheap', 'damaged'}


@lru_cache
def get_sentiment_pipeline():
    return pipeline('sentiment-analysis', model=settings.hf_model_name)


def infer_theme(text: str) -> str:
    text_lower = text.lower()
    for theme, words in THEME_KEYWORDS.items():
        if any(word in text_lower for word in words):
            return theme
    return 'other'


def extract_keywords(text: str, limit: int = 5) -> list[str]:
    tokens = re.findall(r"[a-zA-Z']+", text.lower())
    filtered = [t for t in tokens if len(t) > 3]
    counts = Counter(filtered)
    return [word for word, _ in counts.most_common(limit)]


def classify_sentiment(text: str) -> tuple[str, float]:
    result = get_sentiment_pipeline()(text[:512])[0]
    label = result['label'].lower()
    score = float(result['score'])

    if label == 'positive':
        return 'positive', score
    if label == 'negative':
        return 'negative', score
    return 'neutral', score


def fallback_investment_status(avg_sentiment: float | None, negative_count: int, positive_count: int) -> str:
    if avg_sentiment is None:
        return 'monitor'
    if avg_sentiment >= 0.75 and positive_count >= negative_count:
        return 'promote'
    if negative_count > positive_count:
        return 'improve'
    return 'monitor'
