from datetime import date
from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    product_id: int | None = None


class ProductOut(BaseModel):
    id: int
    organization_id: int | None = None
    product_name: str
    category: str | None = None
    brand: str | None = None
    price: float | None = None

    class Config:
        from_attributes = True


class ReviewOut(BaseModel):
    id: int
    product_id: int
    review_date: date | None = None
    rating: float | None = None
    source: str
    review_title: str | None = None
    review_text: str

    class Config:
        from_attributes = True


class ProductSummaryOut(BaseModel):
    product_id: int
    avg_sentiment: float | None = None
    positive_review_count: int
    negative_review_count: int
    neutral_review_count: int
    total_review_count: int
    estimated_revenue: float | None = None
    top_complaints: list[str] | None = None
    top_praises: list[str] | None = None
    recommendation: str | None = None
    marketing_focus: str | None = None
    improvement_priority: str | None = None
    investment_status: str | None = None

    class Config:
        from_attributes = True


class TrendOut(BaseModel):
    trend_week: date
    keyword: str
    direction: str
    mention_count: int
    source: str | None = None

    class Config:
        from_attributes = True


class PlanOut(BaseModel):
    plan_code: str
    plan_name: str
    target_company_size: str
    monthly_price: float | None = None
    max_user_seats: int | None = None
    max_products: int | None = None
    description: str | None = None

    class Config:
        from_attributes = True


class OrganizationOut(BaseModel):
    id: int
    organization_name: str
    industry_vertical: str
    business_model: str
    brand_stage: str
    website_url: str | None = None
    plan: PlanOut | None = None

    class Config:
        from_attributes = True


class AppConfigOut(BaseModel):
    product_name: str
    vertical: str
    ideal_customer: str
    memberships: list[PlanOut]
