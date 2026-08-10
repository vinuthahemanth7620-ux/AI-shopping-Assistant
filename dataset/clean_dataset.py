import os
import sys
import re
import ast
import json
import numpy as np
import pandas as pd

# Ensure UTF-8 output encoding for Windows terminals
sys.stdout.reconfigure(encoding='utf-8')

# Resolve paths
script_dir = os.path.dirname(os.path.abspath(__file__))
input_file_path = os.path.join(script_dir, "train-00000-of-00001.parquet")

if not os.path.exists(input_file_path):
    input_file_path = "train-00000-of-00001.parquet"

cleaned_dir = os.path.join(script_dir, "cleaned")
output_parquet_path = os.path.join(cleaned_dir, "amazon_cleaned.parquet")
output_csv_path = os.path.join(cleaned_dir, "amazon_cleaned.csv")

# ------------------------------------------------------------
# HELPER FUNCTIONS FOR COLUMN CLEANING
# ------------------------------------------------------------

def clean_list_column(val):
    """Convert array/list/string into a clean pipe-separated string."""
    if val is None:
        return ""
    if isinstance(val, (float, int)):
        if pd.isna(val):
            return ""
        return str(val).strip()
    if isinstance(val, (list, np.ndarray)):
        items = [str(x).strip() for x in val if x is not None and str(x).strip()]
        return " | ".join(items)
    if isinstance(val, str):
        v = val.strip()
        if v.startswith("array(") or v == "":
            return ""
        return v
    return ""


def clean_details_column(val):
    """Convert dictionary-like strings to valid JSON text where possible."""
    if val is None:
        return ""
    if isinstance(val, (float, int)):
        if pd.isna(val):
            return ""
        return str(val).strip()
    if isinstance(val, dict):
        return json.dumps(val)
    if isinstance(val, str):
        v = val.strip()
        if not v:
            return ""
        try:
            parsed = ast.literal_eval(v)
            if isinstance(parsed, dict):
                return json.dumps(parsed)
        except Exception:
            try:
                parsed = json.loads(v)
                if isinstance(parsed, dict):
                    return json.dumps(parsed)
            except Exception:
                pass
        return v
    return ""


def clean_image_column(val):
    """Extract clean URL(s) from markdown-style image links or strings."""
    if val is None or not isinstance(val, str):
        return ""
    # Extract HTTP/HTTPS URLs from Markdown links or raw text
    urls = re.findall(r'https?://[^\s\)"\]]+', val)
    if urls:
        # Preserve order while deduplicating URLs
        unique_urls = list(dict.fromkeys(urls))
        return " | ".join(unique_urls)
    return val.strip()


# ------------------------------------------------------------
# 1. LOAD DATASET
# ------------------------------------------------------------
print("=" * 60)
print("1. LOADING DATASET")
print("=" * 60)

print(f"Loading original dataset from: {input_file_path}")
df = pd.read_parquet(input_file_path)
initial_rows = len(df)
print(f"Initial row count: {initial_rows}")
print(f"Initial column count: {len(df.columns)}")

# Record initial timestamp of original file to verify safety later
original_file_mtime = os.path.getmtime(input_file_path)


# ------------------------------------------------------------
# 2. STANDARDIZE COLUMN NAMES
# ------------------------------------------------------------
print("\n" + "=" * 60)
print("2. STANDARDIZING COLUMN NAMES")
print("=" * 60)

df.columns = [col.lower().strip().replace(' ', '_') for col in df.columns]
print("Standardized columns:", list(df.columns))


# ------------------------------------------------------------
# 3. TITLE CLEANING
# ------------------------------------------------------------
print("\n" + "=" * 60)
print("3. CLEANING TITLES")
print("=" * 60)

df['title'] = df['title'].fillna("").astype(str).str.strip()
df['title'] = df['title'].apply(lambda x: re.sub(r'\s+', ' ', x))

# Filter out empty titles
empty_titles_count = (df['title'] == "").sum()
print(f"Empty titles found: {empty_titles_count}")
df = df[df['title'] != ""].copy()
print(f"Rows remaining after removing empty titles: {len(df)}")


# ------------------------------------------------------------
# 4. DESCRIPTION CLEANING
# ------------------------------------------------------------
print("\n" + "=" * 60)
print("4. CLEANING DESCRIPTIONS")
print("=" * 60)

df['description'] = df['description'].fillna("").astype(str).str.strip()
df['description'] = df['description'].apply(lambda x: re.sub(r'\s+', ' ', x))
print("Descriptions cleaned successfully.")


# ------------------------------------------------------------
# 5. MAIN CATEGORY CLEANING
# ------------------------------------------------------------
print("\n" + "=" * 60)
print("5. CLEANING MAIN CATEGORY")
print("=" * 60)

def clean_main_category(val):
    if val is None or pd.isna(val):
        return "Unknown"
    v = str(val).strip()
    if not v or v.lower() == 'nan' or v.lower() == 'none':
        return "Unknown"
    return v

df['main_category'] = df['main_category'].apply(clean_main_category)
unknown_categories_count = (df['main_category'] == "Unknown").sum()
print(f"Products with 'Unknown' main_category: {unknown_categories_count}")


# ------------------------------------------------------------
# 6. STORE CLEANING
# ------------------------------------------------------------
print("\n" + "=" * 60)
print("6. CLEANING STORE")
print("=" * 60)

def clean_store(val):
    if val is None or pd.isna(val):
        return "Unknown"
    v = str(val).strip()
    if not v or v.lower() == 'nan' or v.lower() == 'none':
        return "Unknown"
    return v

df['store'] = df['store'].apply(clean_store)
unknown_stores_count = (df['store'] == "Unknown").sum()
print(f"Products with 'Unknown' store: {unknown_stores_count}")


# ------------------------------------------------------------
# 7. PRICE CLEANING
# ------------------------------------------------------------
print("\n" + "=" * 60)
print("7. CLEANING PRICE")
print("=" * 60)

df['price'] = pd.to_numeric(df['price'], errors='coerce')
# Negative prices become NaN
df.loc[df['price'] < 0, 'price'] = np.nan
print(f"Missing prices count: {df['price'].isnull().sum()}")
print(f"Valid positive prices count: {(df['price'] > 0).sum()}")


# ------------------------------------------------------------
# 8. AVERAGE RATING CLEANING
# ------------------------------------------------------------
print("\n" + "=" * 60)
print("8. CLEANING AVERAGE RATING")
print("=" * 60)

df['average_rating'] = pd.to_numeric(df['average_rating'], errors='coerce')
# Valid ratings must be between 1.0 and 5.0
invalid_ratings = ~df['average_rating'].between(1.0, 5.0) & df['average_rating'].notnull()
if invalid_ratings.sum() > 0:
    print(f"Setting {invalid_ratings.sum()} out-of-bounds ratings to NaN.")
    df.loc[invalid_ratings, 'average_rating'] = np.nan
else:
    print("All numeric average ratings are within valid [1.0, 5.0] range.")


# ------------------------------------------------------------
# 9. RATING NUMBER CLEANING
# ------------------------------------------------------------
print("\n" + "=" * 60)
print("9. CLEANING RATING NUMBER")
print("=" * 60)

df['rating_number'] = pd.to_numeric(df['rating_number'], errors='coerce').fillna(0)
# Negative values become 0
df.loc[df['rating_number'] < 0, 'rating_number'] = 0
print(f"Rating numbers processed. Missing/negative set to 0. Mean reviews: {df['rating_number'].mean():.2f}")


# ------------------------------------------------------------
# 10. CATEGORIES CLEANING
# ------------------------------------------------------------
print("\n" + "=" * 60)
print("10. CLEANING CATEGORIES")
print("=" * 60)

df['categories'] = df['categories'].apply(clean_list_column)
print("Categories converted to pipe-separated text strings.")


# ------------------------------------------------------------
# 11. FEATURES CLEANING
# ------------------------------------------------------------
print("\n" + "=" * 60)
print("11. CLEANING FEATURES")
print("=" * 60)

df['features'] = df['features'].apply(clean_list_column)
print("Features converted to pipe-separated text strings.")


# ------------------------------------------------------------
# 12. DETAILS CLEANING
# ------------------------------------------------------------
print("\n" + "=" * 60)
print("12. CLEANING DETAILS")
print("=" * 60)

df['details'] = df['details'].apply(clean_details_column)
print("Details converted to valid JSON text where applicable.")


# ------------------------------------------------------------
# 13. IMAGE CLEANING
# ------------------------------------------------------------
print("\n" + "=" * 60)
print("13. CLEANING IMAGE URLS")
print("=" * 60)

df['image'] = df['image'].apply(clean_image_column)
print("Image URLs cleaned and extracted successfully.")


# ------------------------------------------------------------
# 14. DUPLICATES REMOVAL
# ------------------------------------------------------------
print("\n" + "=" * 60)
print("14. REMOVING DUPLICATES BY TITLE")
print("=" * 60)

rows_before_dedup = len(df)
# Normalize title for duplicate checking
df['norm_title'] = df['title'].str.lower().str.strip()

df = df.drop_duplicates(subset=['norm_title'], keep='first').copy()
df.drop(columns=['norm_title'], inplace=True)

rows_after_dedup = len(df)
duplicates_removed = rows_before_dedup - rows_after_dedup

print(f"Rows before deduplication: {rows_before_dedup}")
print(f"Duplicate rows removed:   {duplicates_removed}")
print(f"Rows after deduplication:  {rows_after_dedup}")


# ------------------------------------------------------------
# 15. VALIDATION & METRICS
# ------------------------------------------------------------
print("\n" + "=" * 60)
print("15. VALIDATION METRICS")
print("=" * 60)

print(f"Rows before cleaning:              {initial_rows}")
print(f"Rows after cleaning:               {len(df)}")
print(f"Final columns:                     {list(df.columns)}")
print(f"Duplicate titles remaining:        {df['title'].str.lower().str.strip().duplicated().sum()}")
print(f"Minimum price:                     {df['price'].min()}")
print(f"Maximum price:                     {df['price'].max()}")
print(f"Median price:                      {df['price'].median():.2f}")
print(f"Minimum rating:                    {df['average_rating'].min()}")
print(f"Maximum rating:                    {df['average_rating'].max()}")
print(f"Products with missing price:       {df['price'].isnull().sum()}")
print(f"Products with missing category:    {(df['main_category'] == 'Unknown').sum()}")

print("\nMissing values per column:")
print(df.isnull().sum().to_string())

print("\nNumber of products per main_category:")
print(df['main_category'].value_counts().to_string())


# ------------------------------------------------------------
# 16. DATA QUALITY CHECKS
# ------------------------------------------------------------
print("\n" + "=" * 60)
print("16. DATA QUALITY CHECKS")
print("=" * 60)

assert (df['title'].str.strip() == "").sum() == 0, "Quality Check Failed: Empty titles exist!"
assert df['title'].str.lower().str.strip().duplicated().sum() == 0, "Quality Check Failed: Duplicate normalized titles exist!"
assert df['average_rating'].dropna().between(1.0, 5.0).all(), "Quality Check Failed: Invalid rating values!"
assert (df['price'].dropna() >= 0).all(), "Quality Check Failed: Negative prices exist!"
assert (df['rating_number'] >= 0).all(), "Quality Check Failed: Negative rating numbers exist!"
assert df['categories'].apply(lambda x: isinstance(x, str)).all(), "Quality Check Failed: Non-string category value!"
assert df['features'].apply(lambda x: isinstance(x, str)).all(), "Quality Check Failed: Non-string feature value!"

print("ALL DATA QUALITY CHECKS PASSED SUCCESSFULLY!")


# ------------------------------------------------------------
# 17. SAVING CLEANED OUTPUT
# ------------------------------------------------------------
print("\n" + "=" * 60)
print("17. SAVING CLEANED DATASET")
print("=" * 60)

os.makedirs(cleaned_dir, exist_ok=True)

print(f"Saving Parquet dataset to: {output_parquet_path}")
df.to_parquet(output_parquet_path, index=False)

print(f"Saving CSV dataset to:     {output_csv_path}")
df.to_csv(output_csv_path, index=False)


# ------------------------------------------------------------
# 18. SAFETY VERIFICATION
# ------------------------------------------------------------
print("\n" + "=" * 60)
print("18. SAFETY VERIFICATION")
print("=" * 60)

current_file_mtime = os.path.getmtime(input_file_path)
assert current_file_mtime == original_file_mtime, "SAFETY ERROR: Original Parquet file was modified!"
print("CONFIRMED: Original Parquet file was NOT modified.")

print("\n" + "=" * 60)
print("CLEANING COMPLETED SUCCESSFULLY!")
print("=" * 60)
