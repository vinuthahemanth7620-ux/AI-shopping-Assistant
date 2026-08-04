# 3-Week Project Development Roadmap

This roadmap breaks down the development of the **AI Shopping Assistant** over 3 weeks for **2 Students (Student A & Student B)**.

---

## 🗓️ WEEK 1: Project Foundation, Database, Catalog & Authentication

### Core Focus
Build core application structure, database schema, catalog browsing, and user authentication.

#### Student A (Backend & Database Lead)
- [x] **Day 1**: Project Scaffolding & Application Factory Setup (Completed).
- [x] **Day 1**: MySQL Schema Creation (`database/schema.sql`) & Seed Script (`sample_data.sql`).
- [ ] **Day 2-3**: Implement SQLAlchemy models and Database Migrations (`Flask-Migrate`).
- [ ] **Day 4-5**: Implement Authentication logic (Password hashing with Werkzeug, Login/Register session handlers in `auth_routes.py`).
- [ ] **Day 6-7**: Implement Product CRUD & Search APIs in `product_routes.py`.

#### Student B (Frontend & Design Lead)
- [x] **Day 1**: Design System CSS (`style.css`), Master `base.html`, Navbar, Footer components (Completed).
- [ ] **Day 2-3**: Build Login (`login.html`) and Register (`register.html`) UI templates with Bootstrap 5 validation.
- [ ] **Day 4-5**: Build Product Catalog grid view (`products.html`) with category filters and search bar integration.
- [ ] **Day 6-7**: Build Product Details page (`product_detail.html`) with specifications rendering table.

---

## 🗓️ WEEK 2: Cart System, Comparison Matrix & Shopping Planner

### Core Focus
Build interactive shopping tools: Shopping Cart, Comparison Engine, and Budget Shopping Planner.

#### Student A (Backend & Logic)
- [ ] **Day 8-9**: Build Cart management backend API endpoints (`/cart/add`, `/cart/update`, `/cart/remove`).
- [ ] **Day 10-11**: Implement Product Comparison matrix engine (`compare_routes.py`) to parse JSON specs.
- [ ] **Day 12-14**: Build Shopping Planner database logic and budget calculation algorithms (`cart_routes.py`).

#### Student B (Frontend & Interactive UI)
- [ ] **Day 8-9**: Design Shopping Cart page (`cart.html`) with interactive quantity buttons and price summary sidebar.
- [ ] **Day 10-11**: Design Side-by-Side Product Comparison page (`compare.html`) with spec highlight diffs.
- [ ] **Day 12-14**: Design Shopping Planner interface (`planner.html`) with budget progress indicators.

---

## 🗓️ WEEK 3: AI Integration (Gemini), Analytics, Polish & Testing

### Core Focus
Integrate Gemini API, conversational UI, end-to-end integration testing, and project documentation.

#### Student A (AI & Integration Lead)
- [ ] **Day 15-17**: Integrate Gemini API SDK (`google-generativeai`) in `ai_routes.py` with custom shopping prompts.
- [ ] **Day 18-19**: Build Recommendation engine scoring and save conversation history to `chat_history` table.
- [ ] **Day 20-21**: Backend unit testing, security auditing, and bug fixes.

#### Student B (UI Polish & Presentation Lead)
- [ ] **Day 15-17**: Build AI Chatbot conversational UI (`assistant.html`) with real-time response rendering and prompt suggestions.
- [ ] **Day 18-19**: Build User Profile page (`profile.html`) with saved AI recommendations and chat history log.
- [ ] **Day 20-21**: Responsive UI testing, cross-browser compatibility check, and preparation of presentation slides.
