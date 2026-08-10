import os
import sys
import re
import pandas as pd

# Ensure parent directory is in sys.path so 'app' can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.category import Category

# Ensure UTF-8 output encoding for Windows terminals
sys.stdout.reconfigure(encoding='utf-8')

# Resolve path to cleaned parquet dataset
script_dir = os.path.dirname(os.path.abspath(__file__))
cleaned_file_path = os.path.join(script_dir, "cleaned", "amazon_cleaned.parquet")

if not os.path.exists(cleaned_file_path):
    cleaned_file_path = "cleaned/amazon_cleaned.parquet"


def generate_unique_slug(name, existing_slugs):
    """Generate a clean, URL-safe, unique lowercase slug."""
    slug_base = name.lower().strip()
    slug_base = slug_base.replace('&', 'and')
    slug_base = re.sub(r'[^a-z0-9\s-]', '', slug_base)
    slug_base = re.sub(r'[\s_]+', '-', slug_base)
    slug_base = re.sub(r'-+', '-', slug_base).strip('-')
    
    if not slug_base:
        slug_base = "category"

    slug = slug_base
    counter = 1
    while slug in existing_slugs:
        slug = f"{slug_base}-{counter}"
        counter += 1

    existing_slugs.add(slug)
    return slug


def main():
    app = create_app()
    with app.app_context():
        print("=" * 70)
        print("1. LOADING CLEANED AMAZON DATASET & EXTRACTING CATEGORIES")
        print("=" * 70)

        df = pd.read_parquet(cleaned_file_path)

        # Filter import-eligible products: title non-empty, price > 0, main_category != "Unknown"
        eligible_df = df[
            (df['title'].astype(str).str.strip() != "") &
            (df['price'] > 0) &
            (df['main_category'] != "Unknown")
        ]

        amazon_categories = sorted(eligible_df['main_category'].unique())
        print(f"Extracted {len(amazon_categories)} unique Amazon categories from eligible products.")

        print("\n" + "=" * 70)
        print("2. FETCHING EXISTING DATABASE CATEGORIES")
        print("=" * 70)

        existing_db_cats = Category.query.all()
        existing_before_count = len(existing_db_cats)
        print(f"Existing categories count in database before import: {existing_before_count}")

        # Set of normalized existing names and slugs for fast collision checking
        existing_names_norm = {cat.name.lower().strip(): cat for cat in existing_db_cats}
        existing_slugs = {cat.slug.lower().strip() for cat in existing_db_cats}

        print("\n" + "=" * 70)
        print("3. IMPORT PREVIEW")
        print("=" * 70)
        print(f"{'Category Name':<35} | {'Generated Slug':<32} | {'Action'}")
        print("-" * 75)

        new_categories_to_insert = []
        skipped_count = 0

        for cat_name in amazon_categories:
            norm_name = cat_name.lower().strip()
            if norm_name in existing_names_norm:
                print(f"{cat_name:<35} | {existing_names_norm[norm_name].slug:<32} | SKIPPED (Exists)")
                skipped_count += 1
            else:
                unique_slug = generate_unique_slug(cat_name, existing_slugs)
                new_cat = Category(
                    name=cat_name.strip(),
                    slug=unique_slug,
                    description=f"Amazon product category: {cat_name.strip()}",
                    is_active=True
                )
                new_categories_to_insert.append(new_cat)
                print(f"{cat_name:<35} | {unique_slug:<32} | NEW (To Insert)")

        print("\n" + "=" * 70)
        print("4. EXECUTING DATABASE TRANSACTION")
        print("=" * 70)

        inserted_count = 0
        if new_categories_to_insert:
            try:
                print(f"Inserting {len(new_categories_to_insert)} new Category records...")
                db.session.add_all(new_categories_to_insert)
                db.session.commit()
                inserted_count = len(new_categories_to_insert)
                print("Transaction committed successfully.")
            except Exception as e:
                db.session.rollback()
                print(f"ERROR: Transaction failed. Rolled back changes. Reason: {e}")
                sys.exit(1)
        else:
            print("No new categories to insert. All categories already exist.")

        # Re-fetch all categories from database
        all_categories_after = Category.query.order_by(Category.id).all()
        total_after_count = len(all_categories_after)

        print("\n" + "=" * 70)
        print("5. IMPORT SUMMARY")
        print("=" * 70)
        print(f"Existing categories count before import: {existing_before_count}")
        print(f"New categories inserted:                 {inserted_count}")
        print(f"Categories skipped (already existed):     {skipped_count}")
        print(f"Total categories count after import:      {total_after_count}")

        print("\n" + "=" * 70)
        print("6. FINAL DATABASE CATEGORY LIST")
        print("=" * 70)
        print(f"{'ID':<5} | {'Name':<35} | {'Slug':<32} | {'Active'}")
        print("-" * 80)
        for cat in all_categories_after:
            print(f"{cat.id:<5} | {cat.name:<35} | {cat.slug:<32} | {str(cat.is_active)}")

        print("\n" + "=" * 70)
        print("Amazon category import completed successfully. No products were imported.")
        print("=" * 70)


if __name__ == "__main__":
    main()
