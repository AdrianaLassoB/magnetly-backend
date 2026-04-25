# Base44 integration examples for Magnetly

These examples match the revised product story: **Magnetly for fast growing D2C home goods brands**.

Assume your API is deployed at:

```js
const API_BASE = "https://your-backend-url.com";
```

## 1. Load the app configuration for homepage copy

```js
const config = await fetch(`${API_BASE}/app-config`).then(r => r.json());
console.log(config.product_name);
console.log(config.vertical);
console.log(config.memberships);
```

Use this on the homepage or pricing section to show:
- Magnetly name
- D2C home goods focus
- Growth plan
- Enterprise plan

## 2. Load membership plans for a pricing page

```js
const plans = await fetch(`${API_BASE}/membership-plans`).then(r => r.json());
```

## 3. Load dashboard highlights for the first screen

```js
const highlights = await fetch(`${API_BASE}/dashboard/highlights`).then(r => r.json());
```

Suggested UI cards:
- products tracked
- summaries ready
- products to promote
- products to improve

## 4. Load all products

```js
const products = await fetch(`${API_BASE}/products`).then(r => r.json());
```

## 5. Load one product summary screen

```js
const productId = 1;
const [product, reviews, summary] = await Promise.all([
  fetch(`${API_BASE}/products/${productId}`).then(r => r.json()),
  fetch(`${API_BASE}/products/${productId}/reviews`).then(r => r.json()),
  fetch(`${API_BASE}/products/${productId}/summary`).then(r => r.json()),
]);
```

Suggested fields to show:
- product name
- category
- price
- average sentiment
- estimated revenue
- top complaints
- top praises
- recommendation
- marketing focus
- improvement priority
- investment status

## 6. Trigger review analysis

```js
await fetch(`${API_BASE}/analyze-reviews`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ product_id: 1 })
});
```

## 7. Trigger recommendation generation

```js
await fetch(`${API_BASE}/generate-recommendations/1`, {
  method: "POST"
});
```

## 8. Suggested page structure in Base44

### Homepage
- Magnetly headline
- D2C home goods positioning
- fast rising company pain point
- Growth and Enterprise cards

### Dashboard
- highlights cards
- trend list
- products needing improvement
- products ready to promote

### Products page
- searchable product list
- product status badge
- quick sentiment score

### Product detail page
- review drill down
- complaint themes
- praise themes
- AI recommendation

### Pricing page
- Growth plan
- Enterprise plan
