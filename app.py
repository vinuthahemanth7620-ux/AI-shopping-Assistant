import os
from sqlalchemy import text
from app import create_app, db

app = create_app()

# Database Connection Validation Test on Flask App Startup
with app.app_context():
    try:
        db.session.execute(text("SELECT 1"))
        print("✅ MySQL Database Connected Successfully")

        # Create database tables if they do not exist
        db.create_all()

    except Exception as e:
        print(f"Database connection error: {e}")

if __name__ == "__main__":
    print("Starting AI Shopping Assistant Flask server on http://127.0.0.1:5000")
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=app.config.get("DEBUG", True)
    )