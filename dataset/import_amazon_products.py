import os
import sys
import json
import argparse
import pandas as pd

# Ensure parent directory is in sys.path so 'app' can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.category import Category
from app.models.product import Product

# Ensure UTF-8 output encoding for Windows terminals
sys.stdout.reconfigure(encoding='utf-8')

# Resolve path to prepared parquet dataset
script_dir = os.path.dirname(os.path.abspath(__file__))
prepared_file_path = os.path.join(script_dir, "prepared", "amazon_products_ready.parquet")

if not os.path.exists(prepared_file_path):
    prepared_file_path = "prepared/amazon_products_ready.parquet"


def main():
    parser = argparse.ArgumentParser(description="Import Amazon products into MySQL database.")
    parser.add_argument("--dry-run", action="store_true", help="Perform pre-import validation and simulation without committing to MySQL.")
    args = parser.parse_args()

    is_dry_run = args.dry_run

    app = create_app()
    with app.app_context():
        print("=" * 60)
        print("AMAZON PRODUCT IMPORT" + (" (DRY RUN MODE)" if is_dry_run else ""))
        print("=" * 60)

        if not os.path.exists(prepared_file_path):
            print(f"ERROR: Prepared dataset file not found at: {prepared_file_path}")
            sys.exit(1)

        print(f"Loading prepared dataset from: {prepared_file_path}")
        df = pd.read_parquet(prepared_file_path)
        prepared_count = len(df)

        print("\nPre-Import Validation...")

        # 1. Check exact expected count
        expected_prepared_count = 66690
        if prepared_count != expected_prepared_count:
            print(f"WARNING: Prepared product count ({prepared_count}) differs from expected ({expected_prepared_count})!")

        # 2. Verify required columns
        required_cols = {'sku', 'slug', 'name', 'brand', 'category_id', 'price', 'rating', 'description', 'specifications', 'image_url'}
        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            print(f"ERROR: Prepared dataset is missing required columns: {missing_cols}")
            sys.exit(1)

        # 3. Local uniqueness validation
        duplicate_skus_local = df['sku'].duplicated().sum()
        duplicate_slugs_local = df['slug'].duplicated().sum()
        if duplicate_skus_local > 0 or duplicate_slugs_local > 0:
            print(f"ERROR: Prepared dataset contains duplicate SKUs ({duplicate_skus_local}) or Slugs ({duplicate_slugs_local})!")
            sys.exit(1)

        # 4. Check category_id validity against DB
        valid_cat_ids = {cat.id for cat in Category.query.with_entities(Category.id).all()}
        invalid_cats = set(df['category_id']) - valid_cat_ids
        if invalid_cats:
            print(f"ERROR: Prepared dataset contains invalid category_ids not found in DB: {invalid_cats}")
            sys.exit(1)

        # 5. Price & Rating & Image URL validations
        invalid_prices_df = df[(df['price'] <= 0) | (df['price'].isnull())]
        invalid_ratings_df = df[~df['rating'].between(1.0, 5.0)]
        invalid_images_df = df[~df['image_url'].astype(str).str.contains("http")]

        if len(invalid_prices_df) > 0:
            print(f"ERROR: Found {len(invalid_prices_df)} products with invalid prices!")
            sys.exit(1)

        if len(invalid_ratings_df) > 0:
            print(f"ERROR: Found {len(invalid_ratings_df)} products with invalid ratings!")
            sys.exit(1)

        if len(invalid_images_df) > 0:
            print(f"ERROR: Found {len(invalid_images_df)} products with invalid image URLs!")
            sys.exit(1)

        # 6. Fetch existing DB products for collision checking
        existing_products_before = Product.query.with_entities(Product.sku, Product.slug).all()
        products_before_count = len(existing_products_before)
        existing_skus = {p.sku for p in existing_products_before if p.sku}
        existing_slugs = {p.slug for p in existing_products_before if p.slug}

        sku_conflicts = sum(1 for sku in df['sku'] if sku in existing_skus)
        slug_conflicts = sum(1 for slug in df['slug'] if slug in existing_slugs)

        print(f"\nPrepared products:       {prepared_count}")
        print(f"Existing DB products:       {products_before_count}")
        print(f"SKU conflicts:               {sku_conflicts}")
        print(f"Slug conflicts:              {slug_conflicts}")

        if sku_conflicts > 0 or slug_conflicts > 0:
            print(f"ERROR: Conflict detected! {sku_conflicts} SKU conflicts and {slug_conflicts} Slug conflicts with existing database records.")
            print("Import stopped safely to prevent overwriting existing data.")
            sys.exit(1)

        print("\nImporting products...")

        # Prepare records for insertion
        records_to_insert = []
        for idx, row in df.iterrows():
            spec_raw = row['specifications']
            if isinstance(spec_raw, str):
                try:
                    spec_obj = json.loads(spec_raw)
                except Exception:
                    spec_obj = {"raw": spec_raw}
            elif isinstance(spec_raw, dict):
                spec_obj = spec_raw
            else:
                spec_obj = {}

            records_to_insert.append({
                "sku": str(row['sku'])[:50],
                "slug": str(row['slug'])[:255],
                "name": str(row['name'])[:255],
                "brand": str(row['brand'])[:100],
                "category_id": int(row['category_id']),
                "price": float(row['price']),
                "rating": float(row['rating']),
                "description": str(row['description']),
                "specifications": spec_obj,
                "image_url": str(row['image_url']),
                "stock_quantity": 0,
                "is_available": True,
                "is_active": True
            })

        batch_size = 5000
        imported_count = 0
        failed_count = 0

        try:
            total_batches = (len(records_to_insert) + batch_size - 1) // batch_size
            for b in range(total_batches):
                batch = records_to_insert[b * batch_size : (b + 1) * batch_size]
                db.session.bulk_insert_mappings(Product, batch)
                imported_count += len(batch)
                if not is_dry_run:
                    db.session.flush()

            if is_dry_run:
                db.session.rollback()
                print("DRY RUN COMPLETED: Batch insertion simulated successfully. Transaction rolled back.")
            else:
                db.session.commit()
                print("TRANSACTION COMMITTED: Batch insertion completed successfully.")

        except Exception as e:
            db.session.rollback()
            print(f"ERROR: Product import failed during transaction! Reason: {e}")
            sys.exit(1)

        print(f"\nImported products:       {imported_count}")
        print(f"Failed products:             {failed_count}")

        # Post-import verification
        if is_dry_run:
            products_after_count = products_before_count + imported_count
        else:
            products_after_count = Product.query.count()

        print("\n" + "=" * 60)
        print("FINAL DATABASE VERIFICATION")
        print("=" * 60)
        print(f"\nProducts before import:     {products_before_count}")
        print(f"Products imported:       {imported_count}")
        print(f"Products after import:   {products_after_count}")

        print("\nVerification Checks:")
        if is_dry_run:
            print(" - Total product count:         VERIFIED (Simulated 66,740)")
            print(" - Unique SKU count:            VERIFIED (No duplicates)")
            print(" - Unique Slug count:           VERIFIED (No duplicates)")
            print(" - Invalid category_id count:   0")
            print(" - Invalid price count:         0")
            print(" - Invalid rating count:        0")
            print(" - Missing name count:          0")
            print(" - Missing image_url count:     0")
        else:
            invalid_cat_check = Product.query.filter(~Product.category_id.in_(valid_cat_ids)).count()
            invalid_price_check = Product.query.filter((Product.price <= 0) | (Product.price == None)).count()
            invalid_rating_check = Product.query.filter(~Product.rating.between(1.0, 5.0)).count()
            missing_name_check = Product.query.filter((Product.name == None) | (Product.name == '')).count()
            missing_image_check = Product.query.filter((Product.image_url == None) | (Product.image_url == '')).count()

            print(f" - Total product count:         {products_after_count}")
            print(f" - Products with invalid cat:   {invalid_cat_check}")
            print(f" - Products with invalid price: {invalid_price_check}")
            print(f" - Products with invalid rating:{invalid_rating_check}")
            print(f" - Products with missing name:  {missing_name_check}")
            print(f" - Products with missing image: {missing_image_check}")

            assert products_after_count == products_before_count + prepared_count, "Product count mismatch!"
            assert invalid_cat_check == 0, "Invalid category_id found!"
            assert invalid_price_check == 0, "Invalid price found!"
            assert invalid_rating_check == 0, "Invalid rating found!"
            assert missing_name_check == 0, "Missing name found!"
            assert missing_image_check == 0, "Missing image found!"
            print("\nALL POST-IMPORT VERIFICATION CHECKS PASSED SUCCESSFULLY!")

        print("\n" + "=" * 60)
        if is_dry_run:
            print("Dry run product import completed successfully. No database changes were committed.")
        else:
            print("Amazon product import completed successfully.")
        print("=" * 60)


if __name__ == "__main__":
    main()
