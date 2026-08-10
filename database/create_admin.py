"""
AI Shopping Assistant - Admin Creation Script
Creates or promotes a user account to Admin role with securely hashed credentials.

Usage:
    python database/create_admin.py
    python database/create_admin.py --name "Admin User" --email "admin@example.com" --password "AdminPass123!"
"""

import sys
import os
import argparse
import getpass

# Add parent directory to path so app imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.user import User, UserRole

def create_admin(name=None, email=None, password=None):
    app = create_app()
    with app.app_context():
        print("\n==================================================")
        print("AI SHOPPING ASSISTANT - ADMIN ACCOUNT CREATOR")
        print("==================================================")

        if not name:
            name = input("Enter Admin Full Name: ").strip()
        if not email:
            email = input("Enter Admin Email: ").strip().lower()
        if not password:
            password = getpass.getpass("Enter Admin Password: ").strip()

        if not name or not email or not password:
            print("[ERROR] Name, Email, and Password are all required.")
            sys.exit(1)

        if '@' not in email or '.' not in email:
            print("[ERROR] Please enter a valid email address.")
            sys.exit(1)

        if len(password) < 6:
            print("[ERROR] Password must be at least 6 characters long.")
            sys.exit(1)

        name_parts = name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        base_username = email.split('@')[0]

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            existing_user.role = UserRole.ADMIN
            existing_user.set_password(password)
            existing_user.is_active = True
            db.session.commit()
            print(f"[SUCCESS] User '{email}' was successfully promoted to ADMIN role!")
            return

        new_admin = User(
            username=base_username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=UserRole.ADMIN,
            is_active=True,
            email_verified=True
        )
        new_admin.set_password(password)

        try:
            db.session.add(new_admin)
            db.session.commit()
            print(f"[SUCCESS] Admin account '{email}' created successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] Failed to create admin account: {str(e)}")
            sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Create or promote an Admin account.")
    parser.add_argument('--name', help="Admin full name")
    parser.add_argument('--email', help="Admin email address")
    parser.add_argument('--password', help="Admin password")
    args = parser.parse_args()

    create_admin(name=args.name, email=args.email, password=args.password)
