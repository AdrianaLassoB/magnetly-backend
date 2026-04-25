from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class SubscriptionPlan(Base):
    __tablename__ = 'subscription_plans'

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    plan_name: Mapped[str] = mapped_column(Text, nullable=False)
    target_company_size: Mapped[str] = mapped_column(Text, nullable=False)
    monthly_price: Mapped[float | None] = mapped_column(Numeric(10, 2))
    max_user_seats: Mapped[int | None] = mapped_column(Integer)
    max_products: Mapped[int | None] = mapped_column(Integer)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    organizations = relationship('Organization', back_populates='plan')


class Organization(Base):
    __tablename__ = 'organizations'
    __table_args__ = (
        CheckConstraint("brand_stage IN ('early_growth', 'fast_rising', 'scaled')", name='ck_brand_stage'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_name: Mapped[str] = mapped_column(Text, nullable=False)
    industry_vertical: Mapped[str] = mapped_column(Text, nullable=False, default='D2C Home Goods')
    business_model: Mapped[str] = mapped_column(Text, nullable=False, default='D2C')
    brand_stage: Mapped[str] = mapped_column(String(20), nullable=False, default='fast_rising')
    website_url: Mapped[str | None] = mapped_column(Text)
    plan_id: Mapped[int | None] = mapped_column(ForeignKey('subscription_plans.id'))
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    plan = relationship('SubscriptionPlan', back_populates='organizations')
    users = relationship('AppUser', back_populates='organization')
    data_sources = relationship('DataSource', back_populates='organization')
    products = relationship('Product', back_populates='organization')


class AppUser(Base):
    __tablename__ = 'app_users'

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey('organizations.id', ondelete='SET NULL'))
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(20), default='viewer', nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    organization = relationship('Organization', back_populates='users')


class DataSource(Base):
    __tablename__ = 'data_sources'

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey('organizations.id', ondelete='CASCADE'))
    source_name: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    provider: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_synced_at: Mapped[str | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    organization = relationship('Organization', back_populates='data_sources')


class Product(Base):
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey('organizations.id', ondelete='CASCADE'))
    external_product_id: Mapped[str | None] = mapped_column(Text, unique=True)
    product_name: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(Text)
    brand: Mapped[str | None] = mapped_column(Text)
    price: Mapped[float | None] = mapped_column(Numeric(10, 2))
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    organization = relationship('Organization', back_populates='products')
    reviews = relationship('Review', back_populates='product', cascade='all, delete-orphan')
    transactions = relationship('Transaction', back_populates='product', cascade='all, delete-orphan')
    summary = relationship('ProductSummary', back_populates='product', uselist=False, cascade='all, delete-orphan')


class Transaction(Base):
    __tablename__ = 'transactions'

    id: Mapped[int] = mapped_column(primary_key=True)
    external_transaction_id: Mapped[str | None] = mapped_column(Text, unique=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    order_date: Mapped[str] = mapped_column(Date, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    country: Mapped[str | None] = mapped_column(Text)
    channel: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    product = relationship('Product', back_populates='transactions')


class Review(Base):
    __tablename__ = 'reviews'

    id: Mapped[int] = mapped_column(primary_key=True)
    external_review_id: Mapped[str | None] = mapped_column(Text, unique=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    review_date: Mapped[str | None] = mapped_column(Date)
    rating: Mapped[float | None] = mapped_column(Numeric(3, 2))
    source: Mapped[str] = mapped_column(Text, default='external', nullable=False)
    review_title: Mapped[str | None] = mapped_column(Text)
    review_text: Mapped[str] = mapped_column(Text, nullable=False)
    reviewer_name: Mapped[str | None] = mapped_column(Text)
    market: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    product = relationship('Product', back_populates='reviews')
    analysis = relationship('ReviewAnalysis', back_populates='review', uselist=False, cascade='all, delete-orphan')


class ReviewAnalysis(Base):
    __tablename__ = 'review_analysis'

    id: Mapped[int] = mapped_column(primary_key=True)
    review_id: Mapped[int] = mapped_column(ForeignKey('reviews.id', ondelete='CASCADE'), unique=True, nullable=False)
    sentiment_label: Mapped[str | None] = mapped_column(Text)
    sentiment_score: Mapped[float | None] = mapped_column(Numeric(6, 4))
    theme: Mapped[str | None] = mapped_column(Text)
    keywords: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    analyzed_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    review = relationship('Review', back_populates='analysis')


class ProductSummary(Base):
    __tablename__ = 'product_summary'
    __table_args__ = (
        CheckConstraint("investment_status IN ('promote', 'improve', 'monitor')", name='ck_investment_status'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id', ondelete='CASCADE'), unique=True, nullable=False)
    avg_sentiment: Mapped[float | None] = mapped_column(Numeric(6, 4))
    positive_review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    negative_review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    neutral_review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_revenue: Mapped[float | None] = mapped_column(Numeric(12, 2))
    top_complaints: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    top_praises: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    recommendation: Mapped[str | None] = mapped_column(Text)
    marketing_focus: Mapped[str | None] = mapped_column(Text)
    improvement_priority: Mapped[str | None] = mapped_column(Text)
    investment_status: Mapped[str | None] = mapped_column(String(20))
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    product = relationship('Product', back_populates='summary')


class KeywordTrend(Base):
    __tablename__ = 'keyword_trends'

    id: Mapped[int] = mapped_column(primary_key=True)
    trend_week: Mapped[str] = mapped_column(Date, nullable=False)
    keyword: Mapped[str] = mapped_column(Text, nullable=False)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    mention_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
