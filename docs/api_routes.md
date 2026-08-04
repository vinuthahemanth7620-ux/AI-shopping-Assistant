# REST API Route Specifications

This document outlines the planned RESTful API endpoints for the **AI Shopping Assistant**.

---

## 1. Authentication Blueprint (`/auth`)

| HTTP Method | Endpoint | Purpose | Request Payload | Response Payload |
|---|---|---|---|---|
| `POST` | `/auth/register` | User Account Registration | `{"username", "email", "password", "first_name", "last_name"}` | `{"status": "success", "message": "User registered successfully"}` |
| `POST` | `/auth/login` | Authenticate user & start session | `{"email", "password"}` | `{"status": "success", "user": {"id", "email", "username"}}` |
| `POST` | `/auth/logout` | Terminate user session | None | `{"status": "success", "message": "Logged out"}` |

---

## 2. Product Catalog Blueprint (`/products`)

| HTTP Method | Endpoint | Purpose | Request Payload / Params | Response Payload |
|---|---|---|---|---|
| `GET` | `/products` | Fetch paginated product listing | `?category=laptops&min_price=1000&sort=rating` | `{"products": [...], "total": 12, "page": 1}` |
| `GET` | `/products/<id>` | Fetch detailed product specs | URL Parameter `id` | `{"id": 1, "name": "...", "specifications": {...}}` |
| `GET` | `/products/search` | Full-text query search | `?q=macbook` | `{"query": "macbook", "results": [...]}` |

---

## 3. AI Assistant Blueprint (`/ai`)

| HTTP Method | Endpoint | Purpose | Request Payload | Response Payload |
|---|---|---|---|---|
| `POST` | `/ai/chat` | Send prompt to Gemini Shopping Assistant | `{"message": "Suggest a gaming laptop under ₹150000"}` | `{"response": "...", "intent": "recommendation", "suggested_products": [1, 3]}` |
| `GET` | `/ai/recommendations` | Get personalized AI recommendations | Session Auth | `{"recommendations": [{"product": {...}, "score": 0.95, "reason": "Matches high RAM preference"}]}` |
| `GET` | `/ai/chat-history` | Fetch previous chat logs | Session Auth | `{"history": [{"user_message": "...", "ai_response": "..."}]}` |

---

## 4. Product Comparison Blueprint (`/compare`)

| HTTP Method | Endpoint | Purpose | Request Payload / Params | Response Payload |
|---|---|---|---|---|
| `GET` | `/compare` | View side-by-side spec matrix | `?p1=1&p2=2` | `{"product1": {...}, "product2": {...}, "differences": [...]}` |
| `POST` | `/compare/add` | Add product to compare drawer | `{"product_id": 1}` | `{"status": "success", "compare_list": [1, 2]}` |

---

## 5. Shopping Planner Blueprint (`/planner`)

| HTTP Method | Endpoint | Purpose | Request Payload | Response Payload |
|---|---|---|---|---|
| `GET` | `/planner` | Fetch user shopping plans | Session Auth | `{"plans": [{"id": 1, "plan_name": "College Setup", "budget": 150000}]}` |
| `POST` | `/planner/create` | Create new budget plan | `{"plan_name": "Office Tech", "budget": 200000}` | `{"status": "success", "plan_id": 2}` |
| `POST` | `/planner/optimize` | AI budget allocation optimization | `{"plan_id": 1}` | `{"optimized_items": [...], "total_cost": 142000, "savings": 8000}` |

---

## 6. Cart Blueprint (`/cart`)

| HTTP Method | Endpoint | Purpose | Request Payload | Response Payload |
|---|---|---|---|---|
| `GET` | `/cart` | View current user cart | Session Auth | `{"items": [...], "subtotal": 129990.00}` |
| `POST` | `/cart/add` | Add item to cart | `{"product_id": 1, "quantity": 1}` | `{"status": "success", "cart_count": 1}` |
| `POST` | `/cart/update` | Update item quantity | `{"cart_id": 1, "quantity": 2}` | `{"status": "success"}` |
| `DELETE` | `/cart/remove/<id>`| Remove item from cart | URL Parameter `id` | `{"status": "success"}` |

---

## 7. Profile Blueprint (`/profile`)

| HTTP Method | Endpoint | Purpose | Request Payload | Response Payload |
|---|---|---|---|---|
| `GET` | `/profile` | Get profile details | Session Auth | `{"user": {"id": 1, "email": "...", "username": "..."}}` |
| `PUT` | `/profile/update` | Update user profile info | `{"first_name": "Jane", "last_name": "Doe"}` | `{"status": "success"}` |
