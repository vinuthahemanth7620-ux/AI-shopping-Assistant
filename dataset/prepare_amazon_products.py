import os
import sys
import re
import json
import hashlib
import pandas as pd

# Ensure parent directory is in sys.path so 'app' can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.category import Category
from app.models.product import Product

# Ensure UTF-8 output encoding for Windows terminals
sys.stdout.reconfigure(encoding='utf-8')

# Resolve paths
script_dir = os.path.dirname(os.path.abspath(__file__))
cleaned_file_path = os.path.join(script_dir, "cleaned", "amazon_cleaned.parquet")

if not os.path.exists(cleaned_file_path):
    cleaned_file_path = "cleaned/amazon_cleaned.parquet"

prepared_dir = os.path.join(script_dir, "prepared")
output_parquet_path = os.path.join(prepared_dir, "amazon_products_ready.parquet")
output_csv_path = os.path.join(prepared_dir, "amazon_products_ready.csv")


def generate_deterministic_sku(title, brand, category_id, idx, existing_skus):
    """Generate a deterministic, unique SKU (max 50 chars)."""
    unique_str = f"{idx}:{title}:{brand}:{category_id}"
    hash_digest = hashlib.md5(unique_str.encode('utf-8')).hexdigest()[:12].upper()
    sku_base = f"AMZ-{hash_digest}"
    
    sku = sku_base
    counter = 1
    while sku in existing_skus:
        sku = f"AMZ-{hash_digest}-{counter}"
        counter += 1
    existing_skus.add(sku)
    return sku


def generate_unique_slug(name, existing_slugs):
    """Generate a URL-safe, unique slug (max 255 chars)."""
    slug_base = name.lower().strip()
    slug_base = slug_base.replace('&', 'and')
    slug_base = re.sub(r'[^a-z0-9\s-]', '', slug_base)
    slug_base = re.sub(r'[\s_]+', '-', slug_base)
    slug_base = re.sub(r'-+', '-', slug_base).strip('-')
    
    if not slug_base:
        slug_base = "product"

    # Truncate base to 200 chars to leave space for suffix counters
    slug_base = slug_base[:200].rstrip('-')

    slug = slug_base
    counter = 1
    while slug in existing_slugs:
        suffix = f"-{counter}"
        max_base_len = 255 - len(suffix)
        slug = slug_base[:max_base_len].rstrip('-') + suffix
        counter += 1

    existing_slugs.add(slug)
    return slug


def parse_specifications(features_val, details_val):
    """Combine features and details into a valid JSON-serializable dict."""
    spec = {}
    
    # Process features
    if features_val and isinstance(features_val, str):
        feature_list = [f.strip() for f in features_val.split(" | ") if f.strip()]
        spec["features"] = feature_list
    elif isinstance(features_val, (list, tuple)):
        spec["features"] = [str(x).strip() for x in features_val if x and str(x).strip()]
    else:
        spec["features"] = []

    # Process details
    if details_val and isinstance(details_val, str):
        try:
            parsed_det = json.loads(details_val)
            if isinstance(parsed_det, dict):
                spec["details"] = parsed_det
            else:
                spec["details"] = {"info": str(parsed_det)}
        except Exception:
            spec["details"] = {"raw": details_val}
    elif isinstance(details_val, dict):
        spec["details"] = details_val
    else:
        spec["details"] = {}

    return spec


def main():
    app = create_app()
    with app.app_context():
        print("=" * 70)
        print("1. LOADING CLEANED DATASET")
        print("=" * 70)

        df = pd.read_parquet(cleaned_file_path)
        cleaned_total_rows = len(df)
        print(f"Total cleaned products loaded: {cleaned_total_rows}")

        # Filter import-eligible products
        eligible_df = df[
            (df['title'].astype(str).str.strip() != "") &
            (df['price'] > 0) &
            (df['main_category'] != "Unknown")
        ].copy()

        eligible_count = len(eligible_df)
        print(f"Eligible products count:        {eligible_count}")
        expected_eligible = 66690

        if eligible_count != expected_eligible:
            print(f"WARNING: Eligible product count ({eligible_count}) differs from expected ({expected_eligible})!")
        else:
            print("CONFIRMED: Eligible product count matches expected 66,690 exactly.")

        print("\n" + "=" * 70)
        print("2. LOADING DATABASE CATEGORIES & MAPPING")
        print("=" * 70)

        db_categories = Category.query.all()
        print(f"Loaded {len(db_categories)} categories from MySQL database.")

        # Map normalized name -> category_id and category_name
        cat_name_to_id = {cat.name.lower().strip(): cat.id for cat in db_categories}
        cat_id_to_name = {cat.id: cat.name for cat in db_categories}

        # Check mapping for all Amazon main_categories in eligible_df
        missing_category_mappings = []
        for amz_cat in eligible_df['main_category'].unique():
            norm_cat = amz_cat.lower().strip()
            if norm_cat not in cat_name_to_id:
                count = (eligible_df['main_category'] == amz_cat).sum()
                missing_category_mappings.append((amz_cat, count))

        if missing_category_mappings:
            print("ERROR: Unmapped categories found!")
            for unmapped_cat, count in missing_category_mappings:
                print(f" - Unmapped category: '{unmapped_cat}' (Affects {count} products)")
            print("Stopping preparation process due to category mapping failures.")
            sys.exit(1)
        else:
            print("SUCCESS: All Amazon main_categories successfully mapped to MySQL category IDs.")

        print("\n" + "=" * 70)
        print("3. LOADING EXISTING PRODUCTS FROM MYSQL FOR CONFLICT CHECK")
        print("=" * 70)

        existing_db_products = Product.query.with_entities(Product.sku, Product.slug).all()
        existing_db_skus = {p.sku for p in existing_db_products if p.sku}
        existing_db_slugs = {p.slug for p in existing_db_products if p.slug}
        print(f"Existing MySQL Products: {len(existing_db_products)}")
        print(f"Existing DB SKUs:       {len(existing_db_skus)}")
        print(f"Existing DB Slugs:      {len(existing_db_slugs)}")

        print("\n" + "=" * 70)
        print("4. PREPARING AND VALIDATING PRODUCTS")
        print("=" * 70)

        prepared_records = []
        rejected_count = 0
        invalid_prices_count = 0
        invalid_ratings_count = 0
        invalid_images_count = 0
        category_mapping_failures = 0

        # Sets for tracking local SKU and Slug uniqueness
        used_skus = set()
        # Include existing DB slugs and SKUs so we avoid conflicts with existing records in DB
        used_slugs = set(existing_db_slugs)

        sku_conflicts_with_db = 0
        slug_conflicts_with_db = 0

        for idx, row in eligible_df.reset_index(drop=True).iterrows():
            title = str(row['title']).strip()
            store = str(row['store']).strip()
            main_cat = str(row['main_category']).strip()
            price_val = float(row['price'])
            rating_val = float(row['average_rating']) if pd.notnull(row['average_rating']) else 0.0
            desc_val = str(row['description']).strip() if pd.notnull(row['description']) else ""
            img_val = str(row['image']).strip() if pd.notnull(row['image']) else ""

            # Brand handling & length constraint (max 100 chars for DB VARCHAR(100))
            brand = store if store and store != "Unknown" else "Unknown"
            if len(brand) > 100:
                brand = brand[:100].strip()

            # Name length constraint (max 255 chars for DB VARCHAR(255))
            if len(title) > 255:
                title_clean = title[:255].strip()
            else:
                title_clean = title

            # Category ID mapping
            cat_id = cat_name_to_id.get(main_cat.lower().strip())
            if not cat_id:
                category_mapping_failures += 1
                rejected_count += 1
                continue

            # Price validation
            if price_val <= 0 or price_val >= 100000000.0:  # Fits Numeric(10,2) max 99,999,999.99
                invalid_prices_count += 1
                rejected_count += 1
                continue
            price_rounded = round(price_val, 2)

            # Rating validation
            if rating_val < 0.0 or rating_val > 5.0:
                invalid_ratings_count += 1
                rejected_count += 1
                continue
            rating_rounded = round(rating_val, 2)

            # Image URL validation
            if len(img_val) > 500:
                invalid_images_count += 1
                rejected_count += 1
                continue

            # Specifications parsing
            spec_dict = parse_specifications(row.get('features'), row.get('details'))
            try:
                spec_json_str = json.dumps(spec_dict)
            except Exception as e:
                print(f"ERROR: Specifications JSON serialization failed for row {idx}: {e}")
                rejected_count += 1
                continue

            # SKU generation
            sku = generate_deterministic_sku(title, brand, cat_id, idx, used_skus)
            if sku in existing_db_skus:
                sku_conflicts_with_db += 1

            # Slug generation
            slug = generate_unique_slug(title, used_slugs)

            # Strict field validations
            assert len(title_clean) > 0, "Empty title found!"
            assert 0 < len(brand) <= 100, f"Brand length invalid: {len(brand)}"
            assert cat_id in cat_id_to_name, f"Category ID {cat_id} not in DB!"
            assert price_rounded > 0, "Price <= 0!"
            assert 0.0 <= rating_rounded <= 5.0, "Rating out of range!"
            assert len(sku) <= 50, f"SKU length > 50: {len(sku)}"
            assert len(slug) <= 255, f"Slug length > 255: {len(slug)}"
            assert len(img_val) <= 500, f"Image URL > 500: {len(img_val)}"

            prepared_records.append({
                'sku': sku,
                'slug': slug,
                'name': title_clean,
                'brand': brand,
                'category_id': cat_id,
                'category_name': cat_id_to_name[cat_id],
                'price': price_rounded,
                'rating': rating_rounded,
                'description': desc_val,
                'specifications': spec_json_str,
                'image_url': img_val,
                'stock_quantity': 0,
                'is_available': True,
                'is_active': True
            })

        prepared_df = pd.DataFrame(prepared_records)
        prepared_success_count = len(prepared_df)

        print(f"Validation completed successfully for {prepared_success_count} products.")
        print(f"Local SKU uniqueness verified: {prepared_df['sku'].nunique() == prepared_success_count}")
        print(f"Local Slug uniqueness verified: {prepared_df['slug'].nunique() == prepared_success_count}")

        print("\n" + "=" * 70)
        print("5. DATABASE CONFLICT REPORT")
        print("=" * 70)
        print(f"Existing DB SKUs:           {len(existing_db_skus)}")
        print(f"Existing DB Slugs:          {len(existing_db_slugs)}")
        print(f"SKU Conflicts with DB:      {sku_conflicts_with_db}")
        print(f"Slug Conflicts with DB:     {slug_conflicts_with_db}")

        print("\n" + "=" * 70)
        print("6. PREVIEW OF 10 PREPARED PRODUCTS")
        print("=" * 70)
        
        sample_10 = prepared_df.head(10)
        for i, p in sample_10.iterrows():
            print(f"[{i+1}] SKU:         {p['sku']}")
            print(f"    Slug:        {p['slug']}")
            print(f"    Name:        {p['name']}")
            print(f"    Brand:       {p['brand']}")
            print(f"    Category:    ID {p['category_id']} ({p['category_name']})")
            print(f"    Price:       ${p['price']:.2f}")
            print(f"    Rating:      {p['rating']:.2f}")
            print(f"    Image URL:   {p['image_url']}")
            print(f"    Spec Sample: {p['specifications'][:120]}...")
            print("-" * 60)

        print("\n" + "=" * 70)
        print("7. PREPARATION SUMMARY METRICS")
        print("=" * 70)
        print(f"Total cleaned products:        {cleaned_total_rows}")
        print(f"Eligible products:             {eligible_count}")
        print(f"Prepared successfully:         {prepared_success_count}")
        print(f"Rejected:                      {rejected_count}")
        print(f"SKU conflicts:                 {sku_conflicts_with_db}")
        print(f"Slug conflicts:                {slug_conflicts_with_db}")
        print(f"Category mapping failures:     {category_mapping_failures}")
        print(f"Invalid prices:                {invalid_prices_count}")
        print(f"Invalid ratings:               {invalid_ratings_count}")
        print(f"Invalid image URLs:            {invalid_images_count}")

        print("\n" + "=" * 70)
        print("8. SAVING PREPARED DATASET LOCALLY")
        print("=" * 70)

        os.makedirs(prepared_dir, exist_ok=True)

        print(f"Saving Parquet dataset to: {output_parquet_path}")
        prepared_df.to_parquet(output_parquet_path, index=False)

        print(f"Saving CSV dataset to:     {output_csv_path}")
        prepared_df.to_csv(output_csv_path, index=False)

        print("\n" + "=" * 70)
        print("Product preparation completed. No products were inserted into MySQL.")
        print("=" * 70)


if __name__ == "__main__":
    main()
