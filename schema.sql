CREATE TABLE IF NOT EXISTS subscription_plans (
    id BIGSERIAL PRIMARY KEY,
    plan_code TEXT NOT NULL UNIQUE CHECK (plan_code IN ('growth', 'enterprise')),
    plan_name TEXT NOT NULL,
    target_company_size TEXT NOT NULL,
    monthly_price NUMERIC(10,2),
    max_user_seats INTEGER,
    max_products INTEGER,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS organizations (
    id BIGSERIAL PRIMARY KEY,
    organization_name TEXT NOT NULL,
    industry_vertical TEXT NOT NULL DEFAULT 'D2C Home Goods',
    business_model TEXT NOT NULL DEFAULT 'D2C',
    brand_stage TEXT NOT NULL DEFAULT 'fast_rising' CHECK (brand_stage IN ('early_growth', 'fast_rising', 'scaled')),
    website_url TEXT,
    plan_id BIGINT REFERENCES subscription_plans(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app_users (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT REFERENCES organizations(id) ON DELETE SET NULL,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT,
    role TEXT NOT NULL DEFAULT 'viewer' CHECK (role IN ('admin', 'analyst', 'viewer')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS data_sources (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT REFERENCES organizations(id) ON DELETE CASCADE,
    source_name TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK (source_type IN ('reviews', 'transactions', 'support', 'social_media', 'surveys')),
    provider TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS products (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT REFERENCES organizations(id) ON DELETE CASCADE,
    external_product_id TEXT UNIQUE,
    product_name TEXT NOT NULL,
    category TEXT,
    brand TEXT,
    price NUMERIC(10,2),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS transactions (
    id BIGSERIAL PRIMARY KEY,
    external_transaction_id TEXT UNIQUE,
    product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    order_date DATE NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10,2) NOT NULL CHECK (unit_price >= 0),
    country TEXT,
    channel TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transactions_product_id ON transactions(product_id);
CREATE INDEX IF NOT EXISTS idx_transactions_order_date ON transactions(order_date);

CREATE TABLE IF NOT EXISTS reviews (
    id BIGSERIAL PRIMARY KEY,
    external_review_id TEXT UNIQUE,
    product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    review_date DATE,
    rating NUMERIC(3,2),
    source TEXT NOT NULL DEFAULT 'external',
    review_title TEXT,
    review_text TEXT NOT NULL,
    reviewer_name TEXT,
    market TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reviews_product_id ON reviews(product_id);
CREATE INDEX IF NOT EXISTS idx_reviews_review_date ON reviews(review_date);

CREATE TABLE IF NOT EXISTS review_analysis (
    id BIGSERIAL PRIMARY KEY,
    review_id BIGINT NOT NULL UNIQUE REFERENCES reviews(id) ON DELETE CASCADE,
    sentiment_label TEXT,
    sentiment_score NUMERIC(6,4),
    theme TEXT,
    keywords TEXT[],
    analyzed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS product_summary (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL UNIQUE REFERENCES products(id) ON DELETE CASCADE,
    avg_sentiment NUMERIC(6,4),
    positive_review_count INTEGER NOT NULL DEFAULT 0,
    negative_review_count INTEGER NOT NULL DEFAULT 0,
    neutral_review_count INTEGER NOT NULL DEFAULT 0,
    total_review_count INTEGER NOT NULL DEFAULT 0,
    estimated_revenue NUMERIC(12,2),
    top_complaints TEXT[],
    top_praises TEXT[],
    recommendation TEXT,
    marketing_focus TEXT,
    improvement_priority TEXT,
    investment_status TEXT CHECK (investment_status IN ('promote', 'improve', 'monitor')),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS keyword_trends (
    id BIGSERIAL PRIMARY KEY,
    trend_week DATE NOT NULL,
    keyword TEXT NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ('rising', 'falling', 'stable')),
    mention_count INTEGER NOT NULL DEFAULT 0,
    source TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_keyword_trends_week ON keyword_trends(trend_week);

INSERT INTO subscription_plans (plan_code, plan_name, target_company_size, monthly_price, max_user_seats, max_products, description)
VALUES
    ('growth', 'Growth', 'Small business and fast growing D2C home goods brands', 99.00, 5, 100, 'For small businesses that need product level sentiment, complaint summaries, and a clear dashboard without a large analytics team.'),
    ('enterprise', 'Enterprise', 'Larger companies with more users, data, and product lines', 499.00, 50, 5000, 'For larger brands that need advanced segmentation, deeper trend analysis, more controls, and higher data capacity.')
ON CONFLICT (plan_code) DO NOTHING;
