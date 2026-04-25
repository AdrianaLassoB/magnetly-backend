# Magnetly backend starter

This version is tailored to the product definition you chose.

Magnetly is an AI powered marketing intelligence platform for **fast growing D2C home goods brands** that have grown quickly and no longer manage their product, customer, and marketing information well through spreadsheets alone.

It includes:
- PostgreSQL SQL schema
- FastAPI API
- Hugging Face sentiment analysis
- Gemini recommendation generation
- membership plans for **Growth** and **Enterprise**
- organization records for fast rising D2C home goods brands
- Base44 fetch examples aligned to the product story

## Product fit
Use this backend when your front end needs to show:
- product level complaints and praise
- recommendations on what to improve, promote, or monitor
- D2C home goods focused messaging
- company membership plan details
- dashboard highlights for fast growing brands

## 1. Create a virtual environment and install packages

```bash
python -m venv .venv
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2. Copy environment settings

```bash
cp .env.example .env
```

Then update:
- `DATABASE_URL`
- `GOOGLE_API_KEY`
- `CORS_ORIGINS`

## 3. Create the database schema

Run the SQL inside `schema.sql` against PostgreSQL.

This creates:
- subscription plans
- organizations
- users
- data sources
- products
- transactions
- reviews
- review analysis
- product summaries
- keyword trends

It also seeds two plans:
- `growth`
- `enterprise`

## 4. Start the API

```bash
uvicorn app.main:app --reload
```

Open:
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/health`

## 5. Suggested first workflow

1. Load a D2C home goods organization and assign it a plan.
2. Load products, reviews, and transactions into PostgreSQL.
3. Call `POST /analyze-reviews`.
4. Call `POST /generate-recommendations/{product_id}`.
5. Display results in Base44.

## New endpoints added for the revised product direction

- `GET /app-config`
- `GET /membership-plans`
- `GET /organizations`
- `GET /dashboard/highlights`
- `GET /products`
- `GET /products/{product_id}`
- `GET /products/{product_id}/reviews`
- `GET /products/{product_id}/summary`
- `POST /analyze-reviews`
- `POST /generate-recommendations/{product_id}`
- `GET /trends`

## What changed from the earlier starter

This version is more specific to your positioning:
- D2C home goods focus
- fast rising company profile
- Growth and Enterprise membership structure
- extra organization and plan tables
- dashboard highlights endpoint
- more detailed product summary fields such as revenue, marketing focus, and improvement priority

## Suggested deployment

- Database: Supabase Postgres or Neon
- API host: Render, Railway, or Fly.io
- Front end: Base44
