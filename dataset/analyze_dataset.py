import os
import sys
import pandas as pd

# Ensure UTF-8 output encoding for Windows terminals
sys.stdout.reconfigure(encoding='utf-8')

# Resolve path to parquet dataset file
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, "train-00000-of-00001.parquet")

if not os.path.exists(file_path):
    file_path = "train-00000-of-00001.parquet"

print("Loading dataset...")
df = pd.read_parquet(file_path)

# ============================================================
# 1. CATEGORY ANALYSIS
# ============================================================
print("\n" + "=" * 60)
print("1. CATEGORY ANALYSIS")
print("=" * 60)

unique_categories_count = df['main_category'].nunique(dropna=True)
print(f"Number of unique 'main_category' values: {unique_categories_count}")
print("\nUnique 'main_category' values and product counts (sorted descending):")
cat_counts = df['main_category'].value_counts(dropna=False)
print(cat_counts.to_string())

# ============================================================
# 2. STORE ANALYSIS
# ============================================================
print("\n" + "=" * 60)
print("2. STORE ANALYSIS")
print("=" * 60)

unique_stores_count = df['store'].nunique(dropna=True)
print(f"Number of unique stores: {unique_stores_count}")
print("\nTop 30 stores by product count:")
top_stores = df['store'].value_counts(dropna=False).head(30)
print(top_stores.to_string())

# ============================================================
# 3. PRICE ANALYSIS
# ============================================================
print("\n" + "=" * 60)
print("3. PRICE ANALYSIS")
print("=" * 60)

missing_prices = df['price'].isnull().sum()
positive_prices = (df['price'] > 0).sum()
min_price = df['price'].min()
max_price = df['price'].max()
mean_price = df['price'].mean()
median_price = df['price'].median()
percentiles = df['price'].quantile([0.10, 0.25, 0.50, 0.75, 0.90])

print(f"Number of missing prices: {missing_prices}")
print(f"Number of products with price > 0: {positive_prices}")
print(f"Minimum price: {min_price}")
print(f"Maximum price: {max_price}")
print(f"Mean price: {mean_price:.2f}")
print(f"Median price: {median_price:.2f}")
print("\nPrice Percentiles:")
for pct, val in percentiles.items():
    print(f"  {int(pct * 100)}th percentile: {val:.2f}")

# ============================================================
# 4. RATING ANALYSIS
# ============================================================
print("\n" + "=" * 60)
print("4. RATING ANALYSIS")
print("=" * 60)

min_rating = df['average_rating'].min()
max_rating = df['average_rating'].max()
mean_rating = df['average_rating'].mean()
median_rating = df['average_rating'].median()
rating_counts = df['average_rating'].value_counts().sort_index()

print(f"Minimum average rating: {min_rating}")
print(f"Maximum average rating: {max_rating}")
print(f"Mean average rating: {mean_rating:.2f}")
print(f"Median average rating: {median_rating:.2f}")
print("\nNumber of products for each rating value:")
print(rating_counts.to_string())

# ============================================================
# 5. REVIEW ANALYSIS
# ============================================================
print("\n" + "=" * 60)
print("5. REVIEW ANALYSIS")
print("=" * 60)

missing_reviews = df['rating_number'].isnull().sum()
min_reviews = df['rating_number'].min()
max_reviews = df['rating_number'].max()
mean_reviews = df['rating_number'].mean()
median_reviews = df['rating_number'].median()

print(f"Missing count (rating_number): {missing_reviews}")
print(f"Minimum rating_number: {min_reviews}")
print(f"Maximum rating_number: {max_reviews}")
print(f"Mean rating_number: {mean_reviews:.2f}")
print(f"Median rating_number: {median_reviews:.2f}")

# ============================================================
# 6. DUPLICATE ANALYSIS
# ============================================================
print("\n" + "=" * 60)
print("6. DUPLICATE ANALYSIS")
print("=" * 60)

total_duplicates = df['title'].duplicated().sum()
unique_titles = df['title'].nunique()
title_counts = df['title'].value_counts()
top_duplicate_titles = title_counts[title_counts > 1].head(20)

print(f"Total duplicate titles: {total_duplicates}")
print(f"Number of unique titles: {unique_titles}")
print("\nTop 20 titles occurring more than once:")
print(top_duplicate_titles.to_string())

# ============================================================
# 7. DATA STRUCTURE ANALYSIS
# ============================================================
print("\n" + "=" * 60)
print("7. DATA STRUCTURE ANALYSIS")
print("=" * 60)

for col in ["categories", "features", "details", "image"]:
    print(f"\n--- 5 Example values for '{col}' ---")
    examples = df[col].head(5)
    for i, val in enumerate(examples, 1):
        print(f"Example {i}: {repr(val)}")

# ============================================================
# COMPLETION MESSAGE
# ============================================================
print("\n" + "=" * 60)
print("Analysis completed successfully. Original dataset was not modified.")
print("=" * 60)
