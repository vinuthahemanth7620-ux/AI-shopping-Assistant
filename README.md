# 🛒 AI Shopping Assistant

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.2-green.svg)](https://flask.palletsprojects.com/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple.svg)](https://getbootstrap.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-orange.svg)](https://www.mysql.com/)

An AI-powered e-commerce web application that assists users in making informed purchasing decisions through personalized recommendations, side-by-side product comparisons, budget planning, and interactive AI chatbot assistance.

---

## 📌 Project Overview

- **Project Title**: AI Shopping Assistant
- **Target Audience**: Online Shoppers & Tech Enthusiasts
- **Development Sprint**: 3 Weeks (Final Year Engineering Capstone Project)
- **Team**: 2 Students (Student A & Student B)

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | HTML5, CSS3, Bootstrap 5.3, JavaScript (Vanilla JS), FontAwesome 6 |
| **Backend** | Python Flask (Application Factory Pattern with Modular Blueprints) |
| **Database** | MySQL 8.0 + Flask-SQLAlchemy ORM |
| **AI Integration** | Google Gemini Generative AI API SDK (`google-generativeai`) |
| **Configuration** | `python-dotenv`, Environment variables |

---

## 📁 Project Folder Structure

```text
AI-Shopping-Assistant/
├── app/
│   ├── __init__.py            # Application Factory create_app()
│   ├── models/                # SQLAlchemy Models (User, Category, Product, Cart, etc.)
│   ├── routes/                # Blueprint Route Handlers (Auth, Products, AI, Cart, Planner, etc.)
│   ├── services/              # Business Logic & AI Gemini Integrations
│   ├── utils/                 # Utilities & HTTP Error Handlers
│   ├── static/
│   │   ├── css/style.css       # Core Design System (Amazon/Flipkart inspired)
│   │   ├── js/main.js          # Base Client Scripting
│   │   └── images/            # Static Images
│   └── templates/             # Jinja2 HTML Templates
│       ├── base.html          # Master Base Template
│       ├── components/        # Reusable UI Blocks (Navbar, Footer, Sidebar)
│       ├── main/              # Page Views (index.html)
│       └── errors/            # Custom HTTP Error Pages (404, 500)
├── database/
│   ├── schema.sql             # Full Normalized MySQL DDL Script
│   └── sample_data.sql        # Seed Dataset (Laptops, Mobiles, Headphones, Smart Watches)
├── docs/                      # Comprehensive Architecture & Planning Specs
│   ├── er_diagram.md          # ER Diagram & Relationship Details
│   ├── api_routes.md          # REST API Specification Matrix
│   ├── ui_wireframes.md       # Wireframe & Navigation Flow
│   ├── roadmap.md             # 3-Week Development Roadmap
│   └── coding_standards.md    # Coding Conventions & Best Practices
├── config.py                  # Configuration Classes (Dev, Prod, Test)
├── app.py                     # Application Entrypoint Runner
├── requirements.txt           # Python Package Dependencies
├── .env.example               # Environment Variables Template
├── .gitignore                 # Version Control Exclusions
└── README.md                  # Project Documentation
```

---

## 🚀 Local Installation & Setup Steps

### 1. Prerequisites
- **Python 3.10+** installed.
- **MySQL 8.0+** Server running locally or remotely.
- **Git** version control.

### 2. Clone Repository & Setup Virtual Environment
```bash
git clone https://github.com/your-username/AI-Shopping-Assistant.git
cd AI-Shopping-Assistant

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate virtual environment (Linux/macOS)
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables
Copy `.env.example` to `.env` and fill in your MySQL database credentials:
```bash
cp .env.example .env
```
Edit `.env`:
```ini
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your_secret_key

DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=ai_shopping_assistant

GEMINI_API_KEY=your_gemini_api_key
```

### 5. Setup MySQL Database & Seed Sample Data
Execute the SQL scripts in your MySQL client (e.g. MySQL Workbench, phpMyAdmin, or MySQL CLI):
```bash
mysql -u root -p < database/schema.sql
mysql -u root -p < database/sample_data.sql
```

### 6. Run the Flask Development Server
```bash
python app.py
```
Open your browser and navigate to: **`http://localhost:5000`**

---

## 📖 Module Development Plan (3 Weeks)

- **Week 1**: Foundation setup, Database DDL, User Authentication, Product Catalog & Search.
- **Week 2**: Cart Management, Product Comparison Engine, Shopping Planner with Budget Caps.
- **Week 3**: Gemini AI API Chatbot integration, Recommendation Scoring, UI Polish & Testing.

---

## 📄 License
This project is created for **Final Year Engineering Project Requirements**. All rights reserved.
