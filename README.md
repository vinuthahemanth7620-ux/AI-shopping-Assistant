# 🛍️ AI Shopping Assistant

**AI Shopping Assistant** is an intelligent e-commerce application that combines a rich product catalog with an AI-powered shopping assistant to help users discover relevant products using natural language queries. The platform provides natural language search, recommendation scoring, wishlist and cart management, order checkout, product spec comparison, budget planning, authentication, and an admin dashboard for catalog and order management.

---

## 📌 Project Overview

Online shopping platforms often present thousands of products through rigid category trees and keyword filters, making product discovery tedious. **AI Shopping Assistant** solves this challenge by allowing users to ask questions in normal, everyday English—such as *"Show me a laptop for programming under ₹60,000"* or *"I need a camera for travel photography"*—and receiving ranked, highly relevant product recommendations directly from the MySQL database without needing to understand database categories or search syntax.

---

## ✨ Key Features

### 👤 User Authentication & Security
- User registration and login/logout system powered by Flask-Login.
- Password security hashed using Werkzeug (`generate_password_hash` / `check_password_hash`).
- Automated security email notification on login (`email_service.py`).
- Session security preventing cross-user state leakage.

### 🛍️ Product Catalog & Navigation
- Real product dataset indexed into MySQL categories.
- Detailed product pages featuring high-resolution images, brand tags, pricing in INR (₹), star ratings, and full descriptions.
- Dynamic homepage featuring **Top Categories**, **Featured Products**, **Today's Best Deals**, and **New Arrivals**.

### 🤖 AI Shopping Assistant
- **Natural-Language Query Processing**: Users can query products in plain English without database knowledge.
- **Dynamic Category & Intent Matching**: Parses product categories, budget limits (e.g. *"under ₹50,000"*), rating preferences, and feature keywords.
- **Rule-Based Recommendation Engine**: Multi-tiered candidate retrieval and scoring (0–100%) in `engine.py`.
- **Zero AirPods Bug**: Strict category taxonomy and regex word-boundary filtering ensures non-audio requests (laptops, phones, cameras, shoes) never default to AirPods or earphones.
- **Homepage Integrated Chatbot**: Interactive embedded chatbot widget on the homepage with online indicator, suggestion chips, and instant Add to Cart buttons.

### 🔎 Smart Search & Filtering
- Global search bar wired to `/products/` supporting free-text title, brand, and description searches.
- Category filtering, price range inputs (Min/Max ₹), minimum rating filters (4.5★+, 4.0★+), and sorting options (Price Low-High, High-Low, Newest, Top Rated).

### ❤️ Wishlist Module (End-to-End)
- Heart icon toggles (`♥` filled vs `♡` outline) on product cards reflecting real database state.
- Dynamic navbar wishlist item count badge (`wishlist_item_count`).
- Protected `/wishlist/` page displaying saved items with direct Add to Cart buttons, remove actions, and empty wishlist state.

### 🛒 Shopping Cart System
- Single, unified shopping cart connected to MySQL database for logged-in users.
- Add products, increase/decrease quantities, remove items, and instant cart subtotal calculation.
- Header cart count badge with real-time AJAX updates.

### 📦 Orders & Checkout Pipeline
- Order checkout page (`/orders/checkout`) with address form and order summary.
- Unique order tracking numbers (e.g. `ORD-XXXX`).
- Customer order history (`/orders/`) and detailed single order view (`/orders/<id>`).

### 📊 Product Specs Comparison & Shopping Planner
- **Compare Specs** (`/compare/`): Side-by-side spec comparison table displaying prices, ratings, stock status, and actions.
- **Shopping Planner** (`/planner/`): Budget allocation tool allowing users to set target item caps and total planned budget.

### 👨‍💼 Admin Dashboard & Order Management
- Role-based authorization (`@admin_required`) enforcing admin permissions on the backend.
- Full product CRUD management (Add, Edit, Delete, View) with instant catalog and AI assistant discoverability.
- Admin Customer Order Management (`/admin/orders`) with status update capability (*Pending*, *Processing*, *Shipped*, *Delivered*, *Cancelled*).

### 📱 Responsive UI & Aesthetics
- Responsive layout supporting Desktop (1920x1080), Laptop (1366x768), Tablet (768x1024), and Mobile (390x844).
- Modern aesthetic with curated color palette, smooth transitions, glassmorphism badges, and FontAwesome 6 icons.

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Language** | Python 3.11 | Core application logic |
| **Web Framework** | Flask 3.0.2 | Modular Web Framework & Application Factory |
| **Database** | MySQL 8.0 | Relational Database System |
| **ORM** | SQLAlchemy / Flask-SQLAlchemy | Database ORM & Query Builder |
| **Authentication** | Flask-Login & Werkzeug | User Session & Password Security |
| **Frontend Framework** | HTML5, Vanilla CSS3, Bootstrap 5.3 | Responsive UI Layout & Design System |
| **Client Logic** | JavaScript (Vanilla JS / Fetch API) | AJAX Interactivity, Chatbot, Wishlist Toggles |
| **Icons & Fonts** | FontAwesome 6 & Google Fonts (Inter) | Icons & Typography |
| **Version Control** | Git / GitHub | Codebase Version Control |

---

## 🏗️ System Architecture

```text
User Request (Browser / AJAX)
        ↓
Flask Application Factory (app/__init__.py)
        ↓
Blueprint Route Handlers (auth, main, product, ai, wishlist, cart, order, compare, planner, profile, admin)
        ↓
Presenter / Service Layer (RequirementParser & RecommendationEngine)
        ↓
SQLAlchemy ORM
        ↓
MySQL Database (users, products, categories, cart, wishlists, orders, order_items, shopping_planner, chat_history, login_history)
```

---

## 🗄️ Database Structure

The application uses normalized relational tables in MySQL via SQLAlchemy:

- **`User`** (`users`): System users & administrators (`username`, `email`, `password_hash`, `role`, `is_active`).
- **`Category`** (`categories`): Product categories (`name`, `slug`, `is_active`).
- **`Product`** (`products`): Main product dataset (`name`, `brand`, `price`, `rating`, `stock_quantity`, `description`, `image_url`, `specifications`, `category_id`).
- **`Wishlist`** (`wishlists`): User saved wishlist items (`user_id`, `product_id`, `created_at`).
- **`Cart`** (`cart`): Active cart items per user (`user_id`, `product_id`, `quantity`, `unit_price`).
- **`Order`** (`orders`): Customer placed orders (`order_number`, `user_id`, `total_amount`, `status`, `shipping_address`, `payment_method`).
- **`OrderItem`** (`order_items`): Items within an order (`order_id`, `product_id`, `product_name`, `unit_price`, `quantity`).
- **`ShoppingPlanner`** (`shopping_planner`): Budget planner items (`user_id`, `plan_name`, `budget`, `status`).
- **`ChatHistory`** (`chat_history`): History logs of AI assistant interactions (`user_id`, `user_message`, `ai_response`, `intent`).
- **`LoginHistory`** (`login_history`): Audit logs of user login sessions (`user_id`, `login_time`, `ip_address`, `browser`).

---

## 🤖 AI Shopping Assistant Workflow

```text
User Natural-Language Question ("Show me laptops under ₹60,000 for coding")
        ↓
RequirementParser: Extracts product_type='laptop', max_price=60000, use_case='programming'
        ↓
Dynamic MySQL Category Lookup: Maps category_id in [1, 20]
        ↓
RecommendationEngine: Executes SQL filtering & scoring algorithm
        ↓
RecommendationScorer: Assigns weighted relevance score (0–100%)
        ↓
Formatted Product Cards rendered in Chatbot Panel / AI View
```

---

## 👨‍💼 Admin Workflow

Administrative functionality is protected using role-based authorization, allowing authorized administrators to manage application data, product inventory, customer orders, and contact inquiries.

```text
Admin User Login (role = 'admin')
        ↓
@admin_required Authorization Pass
        ↓
Admin Dashboard (/admin/)
        ↓
Add / Edit / Delete Product, Manage Orders, or Respond to Contact Inquiries
        ↓
MySQL Database Update
        ↓
Product Catalog, Search, and AI Assistant immediately discover updated products
```

---

## 📞 Contact Us

### Project
AI Shopping Assistant

### Support
For technical issues, product-related questions, suggestions, or feedback, please contact our project team.

### Team

#### VINUTHA
**Role**: AI & Python Backend Developer  
**Contribution**: Flask backend, MySQL database, AI Shopping Assistant, authentication, and product management.  
**Email**: vinuthahemanth7620@gmail.com  
**GitHub**: [https://github.com/vinuthahemanth7620](https://github.com/vinuthahemanth7620)  
**LinkedIn**: [https://www.linkedin.com/in/vinutha467304310](https://www.linkedin.com/in/vinutha467304310)  

#### THANUSHREE P.H
**Role**: Frontend & UI/UX Developer  
**Contribution**: UI design, responsive frontend development, product catalog presentation, and user experience.  
**Email**: thanushreeph14@gmail.com  
**GitHub**: [https://github.com/thanushreeph14-del](https://github.com/thanushreeph14-del)  
**LinkedIn**: [https://www.linkedin.com/in/thanushree-ph](https://www.linkedin.com/in/thanushree-ph)  

---

## 🔗 Project Links
- **GitHub Repository**: [vinuthahemanth7620-ux/AI-shopping-Assistant](https://github.com/vinuthahemanth7620-ux/AI-shopping-Assistant)

