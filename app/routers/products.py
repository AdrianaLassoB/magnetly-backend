from collections import Counter
from statistics import mean

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.db import get_db
from app.models import Product, ProductSummary, Review, ReviewAnalysis, Transaction
from app.schemas import AnalyzeRequest, ProductOut, ProductSummaryOut, ReviewOut
from app.services.recommendations import build_prompt, generate_recommendation, parse_recommendation_sections
from app.services.sentiment import classify_sentiment, extract_keywords, fallback_investment_status, infer_theme

router = APIRouter(tags=['products'])


@router.get('/products', response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).order_by(Product.product_name.asc()).all()


@router.get('/products/{product_id}', response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')
    return product


@router.get('/products/{product_id}/reviews', response_model=list[ReviewOut])
def get_product_reviews(product_id: int, db: Session = Depends(get_db)):
    return db.query(Review).filter(Review.product_id == product_id).order_by(Review.review_date.desc().nullslast()).all()


@router.get('/products/{product_id}/summary', response_model=ProductSummaryOut)
def get_product_summary(product_id: int, db: Session = Depends(get_db)):
    summary = db.query(ProductSummary).filter(ProductSummary.product_id == product_id).first()
    if not summary:
        raise HTTPException(status_code=404, detail='Product summary not found. Run analysis first.')
    return summary


@router.post('/analyze-reviews')
def analyze_reviews(payload: AnalyzeRequest, db: Session = Depends(get_db)):
    query = db.query(Review).options(joinedload(Review.analysis))
    if payload.product_id:
        query = query.filter(Review.product_id == payload.product_id)
    reviews = query.all()

    if not reviews:
        raise HTTPException(status_code=404, detail='No reviews found to analyze')

    analyzed_count = 0
    for review in reviews:
        sentiment_label, sentiment_score = classify_sentiment(review.review_text)
        theme = infer_theme(review.review_text)
        keywords = extract_keywords(review.review_text)

        if review.analysis:
            review.analysis.sentiment_label = sentiment_label
            review.analysis.sentiment_score = sentiment_score
            review.analysis.theme = theme
            review.analysis.keywords = keywords
        else:
            analysis = ReviewAnalysis(
                review_id=review.id,
                sentiment_label=sentiment_label,
                sentiment_score=sentiment_score,
                theme=theme,
                keywords=keywords,
            )
            db.add(analysis)
        analyzed_count += 1

    db.commit()
    return {'message': 'Review analysis completed', 'reviews_analyzed': analyzed_count}


@router.post('/generate-recommendations/{product_id}')
def generate_product_recommendation(product_id: int, db: Session = Depends(get_db)):
    product = (
        db.query(Product)
        .options(joinedload(Product.reviews).joinedload(Review.analysis), joinedload(Product.summary), joinedload(Product.transactions))
        .filter(Product.id == product_id)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')

    scored_reviews = [review for review in product.reviews if review.analysis]
    if not scored_reviews:
        raise HTTPException(status_code=400, detail='No analyzed reviews found. Run /analyze-reviews first.')

    sentiments = [float(review.analysis.sentiment_score) for review in scored_reviews]
    avg_sentiment = mean(sentiments) if sentiments else None
    positive_count = sum(1 for review in scored_reviews if review.analysis.sentiment_label == 'positive')
    negative_count = sum(1 for review in scored_reviews if review.analysis.sentiment_label == 'negative')
    neutral_count = sum(1 for review in scored_reviews if review.analysis.sentiment_label == 'neutral')
    total_review_count = len(scored_reviews)

    complaint_words = Counter()
    praise_words = Counter()
    for review in scored_reviews:
        keywords = review.analysis.keywords or []
        if review.analysis.sentiment_label == 'negative':
            complaint_words.update(keywords)
        elif review.analysis.sentiment_label == 'positive':
            praise_words.update(keywords)

    top_complaints = [word for word, _ in complaint_words.most_common(5)]
    top_praises = [word for word, _ in praise_words.most_common(5)]
    estimated_revenue = float(sum(float(tx.quantity) * float(tx.unit_price) for tx in product.transactions)) if product.transactions else None

    prompt = build_prompt(
        product_name=product.product_name,
        category=product.category,
        avg_sentiment=avg_sentiment,
        positive_count=positive_count,
        negative_count=negative_count,
        top_complaints=top_complaints,
        top_praises=top_praises,
        estimated_revenue=estimated_revenue,
    )
    recommendation_text = generate_recommendation(prompt)
    recommendation, why, marketing_focus = parse_recommendation_sections(recommendation_text)
    investment_status = fallback_investment_status(avg_sentiment, negative_count, positive_count)
    improvement_priority = top_complaints[0] if top_complaints else None

    if product.summary:
        product.summary.avg_sentiment = avg_sentiment
        product.summary.positive_review_count = positive_count
        product.summary.negative_review_count = negative_count
        product.summary.neutral_review_count = neutral_count
        product.summary.total_review_count = total_review_count
        product.summary.estimated_revenue = estimated_revenue
        product.summary.top_complaints = top_complaints
        product.summary.top_praises = top_praises
        product.summary.recommendation = recommendation
        product.summary.marketing_focus = marketing_focus or why
        product.summary.improvement_priority = improvement_priority
        product.summary.investment_status = investment_status
        summary = product.summary
    else:
        summary = ProductSummary(
            product_id=product.id,
            avg_sentiment=avg_sentiment,
            positive_review_count=positive_count,
            negative_review_count=negative_count,
            neutral_review_count=neutral_count,
            total_review_count=total_review_count,
            estimated_revenue=estimated_revenue,
            top_complaints=top_complaints,
            top_praises=top_praises,
            recommendation=recommendation,
            marketing_focus=marketing_focus or why,
            improvement_priority=improvement_priority,
            investment_status=investment_status,
        )
        db.add(summary)

    db.commit()
    db.refresh(summary)
    return {'message': 'Recommendation generated', 'summary': ProductSummaryOut.model_validate(summary)}


@router.get('/dashboard/highlights')
def get_dashboard_highlights(db: Session = Depends(get_db)):
    product_count = db.query(func.count(Product.id)).scalar() or 0
    summary_count = db.query(func.count(ProductSummary.id)).scalar() or 0
    promote_count = db.query(func.count(ProductSummary.id)).filter(ProductSummary.investment_status == 'promote').scalar() or 0
    improve_count = db.query(func.count(ProductSummary.id)).filter(ProductSummary.investment_status == 'improve').scalar() or 0
    return {
        'vertical': 'D2C Home Goods',
        'ideal_customer': 'Fast growing brands that need one place to manage customer, product, and marketing signals.',
        'products': product_count,
        'summaries_ready': summary_count,
        'promote_products': promote_count,
        'improve_products': improve_count,
    }
