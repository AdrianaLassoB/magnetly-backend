import os
import re
import time
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# -----------------------------
# Optional Gemini setup
# -----------------------------

try:
    import google.generativeai as genai
except ImportError:
    genai = None


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if genai and GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)


GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]


# -----------------------------
# Request models
# -----------------------------

class ReviewItem(BaseModel):
    review_id: Optional[Any] = None
    product_id: Optional[Any] = None
    product_name: Optional[str] = None
    review_text: Optional[str] = None
    rating: Optional[float] = None
    review_date: Optional[str] = None
    source: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    brand: Optional[str] = None


class AnalyzeReviewsRequest(BaseModel):
    reviews: List[ReviewItem] = Field(default_factory=list)


class ChatRequest(BaseModel):
    question: str
    dataset_summary: Optional[Dict[str, Any]] = None
    calculated_answer: Optional[Dict[str, Any]] = None
    relevant_reviews: Optional[List[Dict[str, Any]]] = None


# -----------------------------
# Sentiment logic
# -----------------------------

POSITIVE_WORDS = [
    "love", "loved", "great", "good", "excellent", "perfect",
    "comfortable", "soft", "beautiful", "amazing", "recommend",
    "happy", "quality", "nice", "fit", "fits", "durable",
    "favorite", "worth", "cute", "easy", "warm", "cozy",
    "stylish", "best", "pleased", "wonderful", "pretty",
    "fast", "quick", "smooth", "well made", "high quality"
]

NEGATIVE_WORDS = [
    "bad", "poor", "terrible", "awful", "cheap", "broken",
    "small", "large", "tight", "loose", "uncomfortable",
    "disappointed", "return", "returned", "defective",
    "scratchy", "thin", "wrong", "late", "damaged",
    "hate", "worst", "rough", "shrunk", "shrinks",
    "faded", "problem", "issue", "slow", "delay",
    "delayed", "missing", "overpriced"
]


def classify_sentiment(text: str) -> Dict[str, Any]:
    text_lower = text.lower()

    positive_count = sum(1 for word in POSITIVE_WORDS if word in text_lower)
    negative_count = sum(1 for word in NEGATIVE_WORDS if word in text_lower)

    if positive_count > negative_count:
        return {
            "sentiment_label": "positive",
            "sentiment_score": 1,
            "sentiment_reason": "Review contains more positive customer language."
        }

    if negative_count > positive_count:
        return {
            "sentiment_label": "negative",
            "sentiment_score": -1,
            "sentiment_reason": "Review contains more negative customer language."
        }

    return {
        "sentiment_label": "neutral",
        "sentiment_score": 0,
        "sentiment_reason": "Review does not strongly lean positive or negative."
    }


# -----------------------------
# D2C theme taxonomy
# -----------------------------

THEME_RULES = {
    "Shipping Delay": {
        "category": "complaint",
        "keywords": [
            "late", "delayed", "delay", "shipping took", "arrived late",
            "took forever", "slow shipping", "slow delivery", "delivery took"
        ],
    },
    "Damaged on Arrival": {
        "category": "complaint",
        "keywords": [
            "damaged", "broken", "cracked", "ripped", "arrived damaged",
            "defective", "scratched"
        ],
    },
    "Missing Parts": {
        "category": "complaint",
        "keywords": [
            "missing", "missing piece", "missing parts", "incomplete"
        ],
    },
    "Wrong Item Received": {
        "category": "complaint",
        "keywords": [
            "wrong item", "wrong color", "wrong size sent", "not what i ordered",
            "different item"
        ],
    },
    "Sizing / Dimensions": {
        "category": "complaint",
        "keywords": [
            "too small", "too big", "runs small", "runs large", "tight",
            "loose", "sizing", "size issue", "fit issue", "smaller than expected",
            "larger than expected"
        ],
    },
    "Cheap Quality": {
        "category": "complaint",
        "keywords": [
            "cheap", "poor quality", "low quality", "thin", "flimsy",
            "not worth", "bad quality", "feels cheap"
        ],
    },
    "Fabric / Material Issue": {
        "category": "complaint",
        "keywords": [
            "fabric", "material", "scratchy", "rough", "itchy",
            "thin material", "shrunk", "shrinks"
        ],
    },
    "Comfort Issue": {
        "category": "complaint",
        "keywords": [
            "uncomfortable", "not comfortable", "stiff", "rough", "tight"
        ],
    },
    "Price Concern": {
        "category": "complaint",
        "keywords": [
            "expensive", "overpriced", "not worth the price", "too much"
        ],
    },
    "Packaging Waste": {
        "category": "complaint",
        "keywords": [
            "packaging", "waste", "too much plastic", "box", "wrapped"
        ],
    },
    "Website / Ordering Issue": {
        "category": "complaint",
        "keywords": [
            "website", "checkout", "order problem", "ordering", "cart"
        ],
    },
    "Customer Support Issue": {
        "category": "complaint",
        "keywords": [
            "customer service", "support", "no response", "representative",
            "help desk"
        ],
    },
    "Return / Refund Issue": {
        "category": "complaint",
        "keywords": [
            "return", "returned", "refund", "exchange"
        ],
    },
    "Color / Appearance Mismatch": {
        "category": "complaint",
        "keywords": [
            "color", "different color", "not as pictured", "looks different",
            "picture", "photo"
        ],
    },
    "Durability Issue": {
        "category": "complaint",
        "keywords": [
            "broke", "fell apart", "wore out", "after washing",
            "didn't last", "not durable"
        ],
    },
    "Loved Design": {
        "category": "praise",
        "keywords": [
            "beautiful", "cute", "stylish", "design", "looks great",
            "pretty", "aesthetic"
        ],
    },
    "Loved Quality": {
        "category": "praise",
        "keywords": [
            "great quality", "good quality", "excellent quality",
            "well made", "durable", "high quality"
        ],
    },
    "Loved Comfort": {
        "category": "praise",
        "keywords": [
            "comfortable", "soft", "cozy", "warm", "comfy"
        ],
    },
    "Loved Fit": {
        "category": "praise",
        "keywords": [
            "fits perfectly", "perfect fit", "true to size", "fits great",
            "great fit"
        ],
    },
    "Loved Price / Value": {
        "category": "praise",
        "keywords": [
            "good price", "great value", "worth it", "affordable"
        ],
    },
    "Loved Sustainability": {
        "category": "praise",
        "keywords": [
            "sustainable", "eco", "eco-friendly", "recycled", "green"
        ],
    },
    "Fast Shipping": {
        "category": "praise",
        "keywords": [
            "fast shipping", "arrived quickly", "quick delivery", "fast delivery"
        ],
    },
    "Would Recommend": {
        "category": "praise",
        "keywords": [
            "recommend", "would buy again", "love it", "favorite"
        ],
    },
}


def classify_theme(text: str, sentiment_label: str) -> Dict[str, Any]:
    text_lower = text.lower()
    best_theme = None
    best_score = 0
    best_category = None
    matched_keywords = []

    for theme, rule in THEME_RULES.items():
        score = 0
        matches = []

        for keyword in rule["keywords"]:
            if keyword in text_lower:
                score += 1
                matches.append(keyword)

        if score > best_score:
            best_score = score
            best_theme = theme
            best_category = rule["category"]
            matched_keywords = matches

    if best_theme:
        return {
            "theme_label": best_theme,
            "theme_category": best_category,
            "theme_confidence": min(1.0, 0.45 + best_score * 0.2),
            "extracted_keywords": matched_keywords,
        }

    if sentiment_label == "positive":
        return {
            "theme_label": "Other Praise",
            "theme_category": "praise",
            "theme_confidence": 0.3,
            "extracted_keywords": [],
        }

    if sentiment_label == "negative":
        return {
            "theme_label": "Other Complaint",
            "theme_category": "complaint",
            "theme_confidence": 0.3,
            "extracted_keywords": [],
        }

    return {
        "theme_label": "Neutral / General Feedback",
        "theme_category": "neutral",
        "theme_confidence": 0.2,
        "extracted_keywords": [],
    }


# -----------------------------
# Keyword extraction
# -----------------------------

STOP_WORDS = {
    "the", "and", "for", "with", "this", "that", "was", "are",
    "you", "but", "not", "have", "has", "had", "very", "from",
    "they", "them", "its", "our", "your", "size", "product",
    "item", "just", "really", "would", "could", "also", "into",
    "than", "then", "were", "been", "because", "about", "there",
    "their", "what", "when", "where", "which", "while", "more",
    "much", "like", "only", "after", "before", "over", "under",
    "again", "still", "even"
}


def extract_keywords(text: str, limit: int = 8) -> List[str]:
    words = re.findall(r"[a-zA-Z']+", text.lower())
    clean_words = [
        word for word in words
        if len(word) > 3 and word not in STOP_WORDS
    ]
    counts = Counter(clean_words)
    return [word for word, _ in counts.most_common(limit)]


def create_short_summary(text: str, theme_label: str, sentiment_label: str) -> str:
    clean_text = text.strip()

    if len(clean_text) > 120:
        clean_text = clean_text[:117] + "..."

    return f"{sentiment_label.title()} review about {theme_label}: {clean_text}"


# -----------------------------
# Review analysis
# -----------------------------

def analyze_single_review(review: ReviewItem) -> Dict[str, Any]:
    text = review.review_text or ""

    sentiment = classify_sentiment(text)
    theme = classify_theme(text, sentiment["sentiment_label"])
    keywords = extract_keywords(text)

    return {
        "review_id": review.review_id,
        "product_id": review.product_id,
        "product_name": review.product_name or "Unknown Product",
        "review_text": text,
        "rating": review.rating,
        "review_date": review.review_date,
        "source": review.source,
        "price": review.price,
        "category": review.category,
        "brand": review.brand,
        "sentiment_label": sentiment["sentiment_label"],
        "sentiment_score": sentiment["sentiment_score"],
        "sentiment_reason": sentiment["sentiment_reason"],
        "theme_label": theme["theme_label"],
        "theme_category": theme["theme_category"],
        "theme_confidence": theme["theme_confidence"],
        "extracted_keywords": list(set(keywords + theme["extracted_keywords"])),
        "short_summary": create_short_summary(
            text=text,
            theme_label=theme["theme_label"],
            sentiment_label=sentiment["sentiment_label"],
        ),
    }


def summarize_analyzed_reviews(analyzed_reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_reviews = len(analyzed_reviews)

    sentiment_counts = Counter(
        review["sentiment_label"] for review in analyzed_reviews
    )

    complaint_counts = Counter(
        review["theme_label"]
        for review in analyzed_reviews
        if review["theme_category"] == "complaint"
    )

    praise_counts = Counter(
        review["theme_label"]
        for review in analyzed_reviews
        if review["theme_category"] == "praise"
    )

    positive_text = " ".join(
        review["review_text"]
        for review in analyzed_reviews
        if review["sentiment_label"] == "positive"
    )

    negative_text = " ".join(
        review["review_text"]
        for review in analyzed_reviews
        if review["sentiment_label"] == "negative"
    )

    product_groups = defaultdict(list)
    for review in analyzed_reviews:
        product_groups[str(review.get("product_id"))].append(review)

    product_summaries = []

    for product_id, reviews in product_groups.items():
        product_name = reviews[0].get("product_name", "Unknown Product")

        ratings = [
            review["rating"] for review in reviews
            if isinstance(review.get("rating"), (int, float))
        ]

        avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else None

        positive_count = sum(1 for r in reviews if r["sentiment_label"] == "positive")
        negative_count = sum(1 for r in reviews if r["sentiment_label"] == "negative")

        top_praise = Counter(
            r["theme_label"] for r in reviews if r["theme_category"] == "praise"
        ).most_common(1)

        top_complaint = Counter(
            r["theme_label"] for r in reviews if r["theme_category"] == "complaint"
        ).most_common(1)

        review_count = len(reviews)
        positive_percent = positive_count / review_count if review_count else 0
        negative_percent = negative_count / review_count if review_count else 0

        product_summaries.append({
            "product_id": product_id,
            "product_name": product_name,
            "review_count": review_count,
            "avg_rating": avg_rating,
            "positive_sentiment_percent": round(positive_percent, 3),
            "negative_sentiment_percent": round(negative_percent, 3),
            "top_praise_theme": top_praise[0][0] if top_praise else None,
            "top_complaint_theme": top_complaint[0][0] if top_complaint else None,
            "price": reviews[0].get("price"),
        })

    product_summaries = add_opportunity_scores(product_summaries)

    products_to_promote = sorted(
        product_summaries,
        key=lambda p: p.get("opportunity_score", 0),
        reverse=True,
    )[:10]

    products_to_monitor = sorted(
        product_summaries,
        key=lambda p: (
            p.get("negative_sentiment_percent", 0),
            p.get("review_count", 0),
        ),
        reverse=True,
    )[:10]

    return {
        "total_reviews": total_reviews,
        "sentiment_breakdown": dict(sentiment_counts),
        "top_complaint_themes": [
            {"theme": theme, "count": count}
            for theme, count in complaint_counts.most_common(10)
        ],
        "top_praise_themes": [
            {"theme": theme, "count": count}
            for theme, count in praise_counts.most_common(10)
        ],
        "top_positive_keywords": [
            {"keyword": keyword, "count": count}
            for keyword, count in Counter(extract_keywords(positive_text, 50)).most_common(10)
        ],
        "top_negative_keywords": [
            {"keyword": keyword, "count": count}
            for keyword, count in Counter(extract_keywords(negative_text, 50)).most_common(10)
        ],
        "product_summaries": product_summaries,
        "products_to_promote": products_to_promote,
        "products_to_monitor": products_to_monitor,
    }


def add_opportunity_scores(product_summaries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not product_summaries:
        return product_summaries

    max_reviews = max(p.get("review_count", 0) for p in product_summaries) or 1
    max_price = max(
        [p.get("price") or 0 for p in product_summaries],
        default=1
    ) or 1

    scored = []

    for product in product_summaries:
        review_count = product.get("review_count", 0)
        avg_rating = product.get("avg_rating") or 0
        positive_sentiment = product.get("positive_sentiment_percent", 0)
        price = product.get("price") or 0

        review_score = review_count / max_reviews
        rating_score = avg_rating / 5
        price_score = price / max_price

        opportunity_score = (
            review_score * 0.35
            + rating_score * 0.30
            + positive_sentiment * 0.25
            + price_score * 0.10
        )

        product["opportunity_score"] = round(opportunity_score, 3)

        if opportunity_score >= 0.70:
            product["opportunity_label"] = "High Potential"
        elif opportunity_score >= 0.45:
            product["opportunity_label"] = "Moderate Potential"
        else:
            product["opportunity_label"] = "Low Potential"

        scored.append(product)

    return scored


def analyze_reviews_payload(request: AnalyzeReviewsRequest) -> Dict[str, Any]:
    analyzed_reviews = [analyze_single_review(review) for review in request.reviews]
    summary = summarize_analyzed_reviews(analyzed_reviews)

    return {
        "reviews": analyzed_reviews,
        "summary": summary,
    }


# -----------------------------
# Gemini helper
# -----------------------------

def call_gemini_with_fallback(prompt: str) -> Dict[str, Any]:
    if not genai:
        return {
            "answer": None,
            "source": "local_fallback",
            "model_used": None,
            "ai_status": "package_missing",
            "error_summary": "google-generativeai package is not installed.",
        }

    if not GOOGLE_API_KEY:
        return {
            "answer": None,
            "source": "local_fallback",
            "model_used": None,
            "ai_status": "missing_api_key",
            "error_summary": "GOOGLE_API_KEY is not configured.",
        }

    last_error = None

    for model_name in GEMINI_MODELS:
        for attempt in range(3):
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                text = getattr(response, "text", None)

                if text and text.strip():
                    return {
                        "answer": text.strip(),
                        "source": "gemini",
                        "model_used": model_name,
                        "ai_status": "available",
                        "error_summary": None,
                    }

                last_error = "Gemini returned an empty response."

            except Exception as error:
                last_error = str(error)

                temporary_error = (
                    "503" in last_error
                    or "429" in last_error
                    or "UNAVAILABLE" in last_error.upper()
                    or "RESOURCE_EXHAUSTED" in last_error.upper()
                    or "timeout" in last_error.lower()
                )

                if temporary_error:
                    time.sleep(2 * (attempt + 1))
                    continue

                break

    return {
        "answer": None,
        "source": "local_fallback",
        "model_used": None,
        "ai_status": "busy",
        "error_summary": last_error,
    }


# -----------------------------
# Chat fallback
# -----------------------------

def build_chat_prompt(request: ChatRequest) -> str:
    return f"""
You are Magnetly's AI assistant.

You are not a general chatbot. You are a D2C customer feedback analyst.

Only use the uploaded product and review data provided below.
Do not invent products, reviews, ratings, sentiment, revenue, or sales.

User question:
{request.question}

Dataset summary:
{request.dataset_summary or {}}

Calculated answer:
{request.calculated_answer or {}}

Relevant review examples:
{request.relevant_reviews or []}

Answer format:
1. Direct answer
2. Supporting numbers
3. Example review evidence if available
4. Recommendation

Keep the answer clear, practical, and business-ready.
"""


def build_local_chat_fallback(request: ChatRequest) -> str:
    question = request.question.lower()
    dataset_summary = request.dataset_summary or {}
    calculated_answer = request.calculated_answer or {}
    relevant_reviews = request.relevant_reviews or []

    answer_type = calculated_answer.get("type")

    if answer_type == "growth_potential":
        top_products = calculated_answer.get("top_products", [])
        return format_growth_potential_answer(top_products)

    if answer_type == "products_to_promote":
        products = calculated_answer.get("products", [])
        return format_product_list_answer(
            title="Products to promote",
            products=products,
            reason="These products have strong review activity, ratings, and positive customer language.",
        )

    if answer_type == "products_to_monitor":
        products = calculated_answer.get("products", [])
        return format_product_list_answer(
            title="Products to monitor",
            products=products,
            reason="These products show repeated complaints, negative sentiment, or weaker ratings.",
        )

    if "complain" in question or "complaint" in question:
        themes = dataset_summary.get("top_complaint_themes", [])
        return format_theme_answer(
            title="Top customer complaints",
            themes=themes,
            relevant_reviews=relevant_reviews,
        )

    if "like" in question or "love" in question or "praise" in question:
        themes = dataset_summary.get("top_praise_themes", [])
        return format_theme_answer(
            title="Top customer praise themes",
            themes=themes,
            relevant_reviews=relevant_reviews,
        )

    total_products = dataset_summary.get("total_products", "unknown")
    total_reviews = dataset_summary.get("total_reviews", "unknown")
    average_rating = dataset_summary.get("average_rating", "unknown")

    return (
        "AI-generated wording is temporarily unavailable, so I am using the uploaded data context instead.\n\n"
        f"I received context for {total_products} products and {total_reviews} reviews. "
        f"The average rating is {average_rating}.\n\n"
        "To answer this more specifically, the frontend should send a calculated_answer object "
        "with the relevant product rankings, themes, or review examples."
    )


def format_growth_potential_answer(top_products: List[Dict[str, Any]]) -> str:
    if not top_products:
        return (
            "AI-generated wording is temporarily unavailable, and I do not have enough calculated product data "
            "to rank growth potential yet."
        )

    lines = [
        "AI-generated wording is temporarily unavailable, so I calculated this from the uploaded product and review data instead.",
        "",
        "Top products with the best growth potential:",
    ]

    for index, product in enumerate(top_products[:5], start=1):
        name = product.get("product_name", "Unknown product")
        score = product.get("opportunity_score", "N/A")
        reviews = product.get("review_count", "N/A")
        rating = product.get("avg_rating", "N/A")
        positive = product.get("positive_sentiment_percent", "N/A")
        praise = product.get("top_praise_theme") or "customer praise"
        complaint = product.get("top_complaint_theme") or "no major complaint theme"

        lines.append(
            f"{index}. {name}\n"
            f"   - Opportunity score: {score}\n"
            f"   - Reviews: {reviews}\n"
            f"   - Average rating: {rating}\n"
            f"   - Positive sentiment: {positive}\n"
            f"   - Main praise theme: {praise}\n"
            f"   - Main risk theme: {complaint}"
        )

    lines.append("")
    lines.append(
        "Recommendation: prioritize the highest-scoring products for marketing campaigns because they combine "
        "customer attention, strong ratings, positive language, and meaningful price potential."
    )

    return "\n".join(lines)


def format_product_list_answer(title: str, products: List[Dict[str, Any]], reason: str) -> str:
    if not products:
        return f"I do not have enough product data to calculate {title.lower()} yet."

    lines = [title + ":", ""]

    for index, product in enumerate(products[:5], start=1):
        name = product.get("product_name", "Unknown product")
        reviews = product.get("review_count", "N/A")
        rating = product.get("avg_rating", "N/A")
        sentiment = product.get("positive_sentiment_percent", "N/A")
        theme = product.get("top_praise_theme") or product.get("top_complaint_theme") or "No theme available"

        lines.append(
            f"{index}. {name}\n"
            f"   - Reviews: {reviews}\n"
            f"   - Average rating: {rating}\n"
            f"   - Positive sentiment: {sentiment}\n"
            f"   - Main theme: {theme}"
        )

    lines.append("")
    lines.append(f"Recommendation: {reason}")

    return "\n".join(lines)


def format_theme_answer(
    title: str,
    themes: List[Dict[str, Any]],
    relevant_reviews: List[Dict[str, Any]],
) -> str:
    if not themes:
        return f"I do not have enough theme data to show {title.lower()} yet."

    lines = [title + ":", ""]

    for index, theme in enumerate(themes[:5], start=1):
        theme_name = theme.get("theme", "Unknown theme")
        count = theme.get("count", "N/A")
        lines.append(f"{index}. {theme_name}: {count} reviews")

    if relevant_reviews:
        lines.append("")
        lines.append("Example review evidence:")
        for review in relevant_reviews[:3]:
            product = review.get("product_name", "Unknown product")
            text = review.get("review_text", "")
            if len(text) > 160:
                text = text[:157] + "..."
            lines.append(f'- {product}: "{text}"')

    lines.append("")
    lines.append(
        "Recommendation: use these themes to decide what to fix, what to promote, and what language to use in marketing."
    )

    return "\n".join(lines)


def chat_payload(request: ChatRequest) -> Dict[str, Any]:
    prompt = build_chat_prompt(request)
    gemini_result = call_gemini_with_fallback(prompt)

    if gemini_result["source"] == "gemini":
        return {
            "answer": gemini_result["answer"],
            "source": "gemini",
            "model_used": gemini_result["model_used"],
            "backend_status": "ok",
            "ai_status": "available",
        }

    fallback_answer = build_local_chat_fallback(request)

    return {
        "answer": fallback_answer,
        "source": "local_fallback",
        "model_used": None,
        "backend_status": "ok",
        "ai_status": gemini_result["ai_status"],
    }