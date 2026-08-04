# UI Page Planning & Navigation Architecture

## 1. Application Navigation Flow Diagram

```text
               +-----------------------+
               |     Landing Page      |
               +-----------+-----------+
                           |
                           v
               +-----------------------+
               |   Login / Register    |
               +-----------+-----------+
                           |
                           v
               +-----------------------+
               |    User Dashboard     |
               +-----------+-----------+
                           |
       +-------------------+-------------------+-------------------+
       |                   |                   |                   |
       v                   v                   v                   v
+--------------+   +---------------+   +---------------+   +---------------+
| Products     |   | AI Assistant  |   | Comparison    |   | Shopping      |
| Catalog      |   | (Gemini Chat) |   | Matrix        |   | Planner       |
+------+-------+   +-------+-------+   +-------+-------+   +-------+-------+
       |                   |                   |                   |
       +-------------------+-------------------+-------------------+
                           |
                           v
               +-----------------------+
               |     Shopping Cart     |
               +-----------+-----------+
                           |
                           v
               +-----------------------+
               |     User Profile      |
               +-----------------------+
```

---

## 2. UI Page Wireframe Descriptions

### 1. Landing Page (`/`)
- **Purpose**: Showcase application capabilities, featured AI tools, top product categories, and quick call-to-action buttons.
- **Main Components**:
  - Hero Banner with gradient background & CTA buttons ("Try AI Assistant", "Explore Products").
  - Feature highlights grid (AI Chatbot, Smart Comparison, Budget Planner, Cart Analytics).
  - Category quick navigation chips (Laptops, Mobiles, Headphones, Smart Watches).
  - Footer with tech stack badges.
- **Expected Actions**: Search products, navigate to AI Assistant, view catalog.

### 2. Authentication Pages (`/auth/login`, `/auth/register`)
- **Purpose**: Allow users to securely log in or create a new shopping assistant account.
- **Main Components**:
  - Centered split card layout.
  - Form fields: Email/Username, Password, Remember Me checkbox.
  - Social / guest login fallback link.

### 3. Dashboard (`/dashboard`)
- **Purpose**: Centralized command hub for signed-in users.
- **Main Components**:
  - Recent AI Recommendations carousel.
  - Saved Shopping Plans summary widget.
  - Recent Chat Conversations shortcut.

### 4. Product Listing (`/products`)
- **Purpose**: Browse and search products with filter controls.
- **Main Components**:
  - Left Sidebar: Category checkboxes, price range slider, rating filters.
  - Top Bar: Search bar, sorting dropdown (Price: Low to High, Rating: High to Low).
  - Main Grid: 3-column product cards with rating badges, image, price, "Add to Cart" and "Compare" buttons.

### 5. Product Details (`/products/<id>`)
- **Purpose**: Display complete product specifications and AI purchasing insights.
- **Main Components**:
  - Left Column: High-resolution image gallery.
  - Right Column: Title, brand badge, price, stock status, ratings, key highlights.
  - Specs Table: JSON specification key-value pairs formatted nicely.
  - AI Section: "Why buy this?" AI generated pros & cons summary.

### 6. AI Assistant Page (`/ai/assistant`)
- **Purpose**: Conversational shopping assistant powered by Gemini AI API.
- **Main Components**:
  - Chat window container with scrollable message thread.
  - User message bubbles (right align) and AI assistant response bubbles (left align).
  - Interactive product recommendation cards embedded directly inside chat responses.
  - Prompt suggestion chips ("Best laptop under ₹60,000", "Compare iPhone 15 vs S24 Ultra").

### 7. Product Comparison (`/compare`)
- **Purpose**: Compare up to 3 products side by side.
- **Main Components**:
  - Top selector bar to add/remove products.
  - Side-by-side spec table highlighting matching and conflicting specs (RAM, Display, Battery, Price).

### 8. Shopping Planner (`/planner`)
- **Purpose**: Set budget targets and allocate funds across multiple desired products.
- **Main Components**:
  - Budget progress bar (Total Budget vs. Selected Items Cost).
  - Item wishlist breakdown.
  - AI "Optimize Budget" button to auto-suggest best value combinations.

### 9. Shopping Cart (`/cart`)
- **Purpose**: Review selected items before simulated checkout.
- **Main Components**:
  - Product list table with quantity steppers and remove buttons.
  - Order Summary sidebar: Subtotal, Estimated Taxes, Savings, Checkout CTA.

### 10. User Profile (`/profile`)
- **Purpose**: Manage account details and saved preferences.
- **Main Components**:
  - User avatar and account stats.
  - Profile edit form (First Name, Last Name, Email).
  - Saved AI Chat logs and recommendation history tab.
