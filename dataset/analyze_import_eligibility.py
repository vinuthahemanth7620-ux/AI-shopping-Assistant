import os
import sys
import pandas as pd

# Ensure UTF-8 output encoding for Windows terminals
sys.stdout.reconfigure(encoding='utf-8')

# Resolve paths
script_dir = os.path.dirname(os.path.abspath(__file__))
cleaned_file_path = os.path.join(script_dir, "cleaned", "amazon_cleaned.parquet")

if not os.path.exists(cleaned_file_path):
    cleaned_file_path = "cleaned/amazon_cleaned.parquet"

print("Loading cleaned dataset...")
df = pd.read_parquet(cleaned_file_path)
total_products = len(df)
print(f"Total products in cleaned dataset: {total_products}")

# ============================================================
# 1. PRODUCT NAME ELIGIBILITY
# ============================================================
print("\n" + "=" * 60)
print("1. PRODUCT NAME ELIGIBILITY")
print("=" * 60)

non_empty_titles = (df['title'].astype(str).str.strip() != "").sum()
empty_titles = total_products - non_empty_titles
print(f"Products with non-empty title: {non_empty_titles}")
print(f"Products with empty title:     {empty_titles}")

# ============================================================
# 2. PRICE ELIGIBILITY
# ============================================================
print("\n" + "=" * 60)
print("2. PRICE ELIGIBILITY")
print("=" * 60)

valid_positive_prices = (df['price'] > 0).sum()
missing_prices = df['price'].isnull().sum()
zero_prices = (df['price'] == 0).sum()
negative_prices = (df['price'] < 0).sum()

print(f"Products with valid positive price (> 0): {valid_positive_prices}")
print(f"Products with missing price (NaN):       {missing_prices}")
print(f"Products with zero price (= 0):           {zero_prices}")
print(f"Products with negative price (< 0):       {negative_prices}")

# ============================================================
# 3. BRAND ELIGIBILITY
# ============================================================
print("\n" + "=" * 60)
print("3. BRAND / STORE ELIGIBILITY")
print("=" * 60)

known_stores = (df['store'].notnull() & (df['store'].astype(str).str.strip() != "") & (df['store'] != "Unknown")).sum()
unknown_stores = total_products - known_stores

print(f"Products with known store/brand:   {known_stores}")
print(f"Products with Unknown/empty store: {unknown_stores}")

# ============================================================
# 4. CATEGORY ELIGIBILITY
# ============================================================
print("\n" + "=" * 60)
print("4. CATEGORY ELIGIBILITY")
print("=" * 60)

known_categories = (df['main_category'].notnull() & (df['main_category'] != "Unknown")).sum()
unknown_categories = total_products - known_categories

print(f"Products with known main_category:   {known_categories}")
print(f"Products with Unknown main_category: {unknown_categories}")

# ============================================================
# 5. RATING ELIGIBILITY
# ============================================================
print("\n" + "=" * 60)
print("5. RATING ELIGIBILITY")
print("=" * 60)

valid_ratings = df['average_rating'].between(1.0, 5.0).sum()
invalid_missing_ratings = total_products - valid_ratings

print(f"Products with valid rating (1.0 to 5.0): {valid_ratings}")
print(f"Products with invalid/missing rating:     {invalid_missing_ratings}")

# ============================================================
# 6. IMAGE ELIGIBILITY
# ============================================================
print("\n" + "=" * 60)
print("6. IMAGE ELIGIBILITY")
print("=" * 60)

valid_images = (df['image'].notnull() & df['image'].astype(str).str.contains("http")).sum()
no_images = total_products - valid_images

print(f"Products with valid HTTP/HTTPS image URL: {valid_images}")
print(f"Products without image URL:               {no_images}")

# ============================================================
# 7. CATEGORY-LEVEL IMPORT ANALYSIS
# ============================================================
print("\n" + "=" * 60)
print("7. CATEGORY-LEVEL IMPORT ANALYSIS")
print("=" * 60)

cat_group = df.groupby('main_category')

cat_analysis = []
for cat_name, group in cat_group:
    tot = len(group)
    pos_price = (group['price'] > 0).sum()
    invalid_price = tot - pos_price
    kn_store = (group['store'] != "Unknown").sum()
    un_store = tot - kn_store
    val_img = (group['image'].notnull() & group['image'].astype(str).str.contains("http")).sum()
    
    # Import eligible: title non-empty, price > 0, category != Unknown
    eligible = (group['title'].astype(str).str.strip() != "") & (group['price'] > 0) & (cat_name != "Unknown")
    eligible_count = eligible.sum()
    importable_pct = (eligible_count / tot * 100) if tot > 0 else 0.0

    cat_analysis.append({
        'main_category': cat_name,
        'total': tot,
        'importable': eligible_count,
        'positive_price': pos_price,
        'invalid_missing_price': invalid_price,
        'known_store': kn_store,
        'unknown_store': un_store,
        'valid_image': val_img,
        'importable_pct': importable_pct
    })

cat_df = pd.DataFrame(cat_analysis)
cat_df = cat_df.sort_values(by='importable', ascending=False)

print(f"{'Category':<32} | {'Total':<6} | {'Eligible':<8} | {'Pos Price':<9} | {'No Price':<8} | {'Kn Store':<8} | {'Val Img':<7} | {'Import %'}")
print("-" * 110)
for _, row in cat_df.iterrows():
    print(f"{row['main_category']:<32} | {row['total']:<6} | {row['importable']:<8} | {row['positive_price']:<9} | {row['invalid_missing_price']:<8} | {row['known_store']:<8} | {row['valid_image']:<7} | {row['importable_pct']:6.1f}%")


# ============================================================
# 8. ESTIMATE FINAL IMPORTABLE PRODUCT COUNT
# ============================================================
print("\n" + "=" * 60)
print("8. ESTIMATE FINAL IMPORTABLE PRODUCT COUNT")
print("=" * 60)

is_eligible_mask = (
    (df['title'].astype(str).str.strip() != "") &
    (df['price'] > 0) &
    (df['main_category'] != "Unknown")
)

eligible_total = is_eligible_mask.sum()
ineligible_total = total_products - eligible_total
eligible_percentage = (eligible_total / total_products) * 100

print(f"Total products in cleaned dataset:       {total_products}")
print(f"Import eligible products count:         {eligible_total} ({eligible_percentage:.2f}%)")
print(f"Ineligible products count (skipped):    {ineligible_total} ({100 - eligible_percentage:.2f}%)")

print("\nBreakdown of why products are ineligible:")
no_title_count = (df['title'].astype(str).str.strip() == "").sum()
no_price_count = (df['price'] <= 0) | (df['price'].isnull())
no_cat_count = (df['main_category'] == "Unknown")

print(f" - Empty titles:                         {no_title_count}")
print(f" - Missing/invalid price (<=0 or NaN):   {no_price_count.sum()}")
print(f" - Missing category ('Unknown'):         {no_cat_count.sum()}")


# ============================================================
# 9. DUPLICATE ANALYSIS
# ============================================================
print("\n" + "=" * 60)
print("9. DUPLICATE ANALYSIS")
print("=" * 60)

norm_title_duplicates = df['title'].astype(str).str.lower().str.strip().duplicated().sum()
print(f"Normalized title duplicate count: {norm_title_duplicates}")
if norm_title_duplicates == 0:
    print("CONFIRMED: All normalized titles are unique.")
else:
    print(f"WARNING: Found {norm_title_duplicates} duplicate normalized titles.")


# ============================================================
# 10. COMPLETION MESSAGE
# ============================================================
print("\n" + "=" * 60)
print("Import eligibility analysis completed. No database changes were made.")
print("=" * 60)
