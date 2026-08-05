# Entity Relationship (ER) Diagram & Database Architecture

## 1. Overview
The **AI Shopping Assistant** database uses a normalized **MySQL 8.0** relational schema to guarantee data integrity, avoid redundancy, and enable fast analytical queries for AI recommendations.

---

## 2. ER Diagram (Mermaid Visual)

```mermaid
erDiagram
    USERS ||--o{ CART : "owns"
    USERS ||--o{ CHAT_HISTORY : "initiates"
    USERS ||--o{ RECOMMENDATIONS : "receives"
    USERS ||--o{ SHOPPING_PLANNER : "creates"

    CATEGORIES ||--|{ PRODUCTS : "contains"
    PRODUCTS ||--o{ CART : "added_to"
    PRODUCTS ||--o{ RECOMMENDATIONS : "recommended_in"

    USERS {
        int id PK
        string username UK
        string email UK
        string password_hash
        string first_name
        string last_name
        enum role
        datetime created_at
        datetime updated_at
    }

    CATEGORIES {
        int id PK
        string name UK
        string slug UK
        text description
        datetime created_at
    }

    PRODUCTS {
        int id PK
        string name
        string brand
        int category_id FK
        decimal price
        decimal rating
        text description
        json specifications
        string image_url
        int stock_quantity
        datetime created_at
        datetime updated_at
    }

    CART {
        int id PK
        int user_id FK
        int product_id FK
        int quantity
        datetime added_at
    }

    CHAT_HISTORY {
        int id PK
        int user_id FK
        text user_message
        text ai_response
        string intent
        datetime created_at
    }

    RECOMMENDATIONS {
        int id PK
        int user_id FK
        int product_id FK
        decimal recommendation_score
        string reason
        datetime created_at
    }

    SHOPPING_PLANNER {
        int id PK
        int user_id FK
        string plan_name
        decimal budget
        date target_date
        json selected_items
        enum status
        datetime created_at
        datetime updated_at
    }
```

---

## 3. Detailed Relationship Explanation

### 1. `users` ↔ `cart` (One-to-Many)
- **Relation**: One User can have multiple items in their Cart.
- **Constraint**: Composite UNIQUE key on `(user_id, product_id)` ensures a product is listed once per user cart with an updated `quantity`.
- **Cascade**: `ON DELETE CASCADE` removes user cart items if the user account is deleted.

### 2. `categories` ↔ `products` (One-to-Many)
- **Relation**: One Category contains multiple Products.
- **Constraint**: `FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT`. A category cannot be deleted if products are assigned to it.

### 3. `products` ↔ `cart` (One-to-Many)
- **Relation**: One Product can be referenced in multiple user carts.
- **Cascade**: `ON DELETE CASCADE` removes cart line items if a product is deleted from the store catalog.

### 4. `users` ↔ `chat_history` (One-to-Many)
- **Relation**: Tracks conversational history between a specific user and Gemini AI assistant.
- **Purpose**: Context retention for multi-turn shopping queries.

### 5. `users` & `products` ↔ `recommendations` (Many-to-Many Junction)
- **Relation**: Stores AI-generated product recommendations for individual users with a confidence score (0.000 to 1.000) and reasoning text.

### 6. `users` ↔ `shopping_planner` (One-to-Many)
- **Relation**: Allows users to save targeted budget planning lists containing product references stored in a structured JSON payload.
