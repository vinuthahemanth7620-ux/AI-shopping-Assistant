# Engineering Coding Standards & Guidelines

This document outlines coding standards, security requirements, and best practices for developing the **AI Shopping Assistant**.

---

## 1. Naming Conventions

### Python Code
- **Variables & Functions**: `snake_case` (e.g., `calculate_budget()`, `product_id`).
- **Classes**: `PascalCase` (e.g., `Product`, `ChatHistory`, `DevelopmentConfig`).
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `SECRET_KEY`, `MAX_CART_ITEMS`).
- **Blueprints**: Short lowercase name suffixed with `_bp` (e.g., `auth_bp`, `ai_bp`).

### HTML / CSS / JS
- **CSS Classes**: `kebab-case` (e.g., `product-card`, `btn-primary-custom`).
- **JS Variables**: `camelCase` (e.g., `cartCount`, `fetchRecommendations()`).
- **Template Files**: Lowercase `snake_case` or `kebab-case` (e.g., `index.html`, `product_detail.html`).

---

## 2. Architectural Blueprint (MVC Pattern)

Follow strict separation of concerns:

- **Model (`app/models/`)**: Represents data structures, database schemas via SQLAlchemy ORM. **No HTML formatting or view logic allowed**.
- **View (`app/templates/`)**: Jinja2 HTML templates for UI presentation.
- **Controller (`app/routes/`)**: Blueprint route handlers that parse user HTTP requests, invoke services, and render template views.
- **Services (`app/services/`)**: Isolated business logic (e.g., Gemini API prompt wrappers, scraping, math calculations).

---

## 3. Database & Query Best Practices

- Always use **SQLAlchemy ORM queries** or parameterized statements to prevent **SQL Injection**.
- Define explicit foreign keys and `ON DELETE` constraints (`CASCADE` or `RESTRICT`).
- Use indexes on columns frequently filtered or sorted (`username`, `email`, `slug`, `price`).

---

## 4. Error Handling Strategy

- Never display raw Python backtraces or database error logs to the client.
- Catch errors gracefully and pass flash alerts using `flash('Error message', 'danger')`.
- All standard HTTP error codes (404, 500, 403) must render clean custom error pages (`templates/errors/`).

---

## 5. Security Guidelines

- **Environment Secrets**: Never commit actual API keys or passwords to GitHub. Use `.env` and reference via `config.py`.
- **Password Hashing**: Store passwords using `werkzeug.security.generate_password_hash` with `pbkdf2:sha256` or `bcrypt`.
- **CSRF & XSS Protection**: Escape dynamic outputs in templates (Jinja auto-escapes HTML).
