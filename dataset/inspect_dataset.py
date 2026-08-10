import pandas as pd
import sys

# Ensure UTF-8 output encoding for Windows terminals
sys.stdout.reconfigure(encoding='utf-8')

file_path = "train-00000-of-00001.parquet"

print("Loading dataset...")
df = pd.read_parquet(file_path)

print("\n" + "=" * 60)
print("DATASET INFORMATION")
print("=" * 60)

print("Number of rows:", len(df))
print("Number of columns:", len(df.columns))

print("\n" + "=" * 60)
print("COLUMN NAMES")
print("=" * 60)

for column in df.columns:
    print(column)

print("\n" + "=" * 60)
print("FIRST 5 ROWS")
print("=" * 60)

print(df.head().to_string())

print("\n" + "=" * 60)
print("DATA TYPES")
print("=" * 60)

print(df.dtypes)

print("\n" + "=" * 60)
print("MISSING VALUES")
print("=" * 60)

print(df.isnull().sum())

print("\n" + "=" * 60)
print("DUPLICATE CHECK")
print("=" * 60)

if "title" in df.columns:
    print("Duplicate titles:", df["title"].duplicated().sum())
else:
    print("Title column not found. Unable to check for duplicate titles.")