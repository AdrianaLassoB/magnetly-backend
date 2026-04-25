from functools import lru_cache
from transformers import pipeline

MODEL_NAME = "distilbert/distilbert-base-uncased-finetuned-sst-2-english"

@lru_cache(maxsize=1)
def get_sentiment_pipeline():
    return pipeline("sentiment-analysis", model=MODEL_NAME)

def analyze_sentiment(text: str) -> dict:
    classifier = get_sentiment_pipeline()
    result = classifier(text)[0]
    return {
        "label": result["label"],
        "score": float(result["score"]),
    }
