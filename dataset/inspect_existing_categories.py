import os
import sys
import re
import pandas as pd

# Ensure parent directory is in sys.path so 'app' can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.category import Category
from app.models.product import Product

# Ensure UTF-8 output encoding for Windows terminals
sys.stdout.reconfigure(encoding='utf-8')

# Resolve path to cleaned parquet dataset
script_dir = os.path.dirname(os.path.abspath(__file__))
cleaned_file_path = os.path.join(script_dir, "cleaned", "amazon_cleaned.parquet")

if not os.path.exists(cleaned_file_path):
    cleaned_file_path = "cleaned/amazon_cleaned.parquet"

app = create_app()

with app.app_context():
    print("=" * 70)
    print("1. EXISTING DATABASE CATEGORIES")
    print("=" * 70)

    existing_categories = Category.query.order_by(Category.id).all()
    print(f"Total number of existing categories: {len(existing_categories)}\n")

    print(f"{'ID':<4} | {'Name':<25} | {'Slug':<25} | {'Active':<6} | {'Products Count'}")
    print("-" * 75)
    for cat in existing_categories:
        prod_count = Product.query.filter_by(category_id=cat.id).count()
        print(f"{cat.id:<4} | {cat.name:<25} | {cat.slug:<25} | {str(cat.is_active):<6} | {prod_count}")

    print("\n" + "=" * 70)
    print("2. AMAZON CATEGORIES & MATCHING ANALYSIS")
    print("=" * 70)

    print("Loading cleaned Amazon dataset...")
    df = pd.read_parquet(cleaned_file_path)

    # Filter import-eligible products: title non-empty, price > 0, main_category != "Unknown"
    eligible_df = df[
        (df['title'].astype(str).str.strip() != "") &
        (df['price'] > 0) &
        (df['main_category'] != "Unknown")
    ]

    amz_cat_counts = eligible_df['main_category'].value_counts()
    print(f"Found {len(amz_cat_counts)} Amazon categories with import-eligible products.\n")

    def classify_amazon_category(amz_cat_name, db_categories):
        amz_norm = amz_cat_name.lower().strip()
        amz_slug = amz_cat_name.lower().strip().replace('&', 'and').replace(' ', '-')
        amz_words = set(re.findall(r'\w+', amz_norm))

        possible_matches = []

        for db_cat in db_categories:
            db_norm = db_cat.name.lower().strip()
            db_slug = db_cat.slug.lower().strip()
            db_words = set(re.findall(r'\w+', db_norm))

            # Exact name or slug match
            if amz_norm == db_norm or amz_slug == db_slug:
                return "EXACT MATCH", db_cat.name

            # Substring or meaningful word overlap match
            if (amz_norm in db_norm or db_norm in amz_norm) and len(amz_norm) >= 4 and len(db_norm) >= 4:
                possible_matches.append(db_cat.name)
            else:
                meaningful_overlap = amz_words.intersection(db_words) - {'all', 'and', 'the', 'for', 'of', 'in', 'home', 'store'}
                if len(meaningful_overlap) > 0:
                    possible_matches.append(db_cat.name)

        if possible_matches:
            # Unique possible matches
            unique_possibles = list(dict.fromkeys(possible_matches))
            return "POSSIBLE MATCH", ", ".join(unique_possibles)

        return "NEW CATEGORY", "None"

    print(f"{'Amazon Category Name':<32} | {'Eligible Products':<18} | {'Classification':<15} | {'DB Match Target'}")
    print("-" * 105)

    exact_matches_count = 0
    possible_matches_count = 0
    new_categories_count = 0

    for amz_cat_name, count in amz_cat_counts.items():
        status, match_target = classify_amazon_category(amz_cat_name, existing_categories)
        if status == "EXACT MATCH":
            exact_matches_count += 1
        elif status == "POSSIBLE MATCH":
            possible_matches_count += 1
        else:
            new_categories_count += 1

        print(f"{amz_cat_name:<32} | {count:<18} | {status:<15} | {match_target}")

    print("\n" + "=" * 70)
    print("3. MATCHING SUMMARY")
    print("=" * 70)
    print(f"Total Amazon Categories Analyzed:  {len(amz_cat_counts)}")
    print(f"  - Exact Matches with DB:        {exact_matches_count}")
    print(f"  - Possible Matches with DB:     {possible_matches_count}")
    print(f"  - New Categories to create:     {new_categories_count}")

    print("\n" + "=" * 70)
    print("Category inspection completed. No database changes were made.")
    print("=" * 70)
