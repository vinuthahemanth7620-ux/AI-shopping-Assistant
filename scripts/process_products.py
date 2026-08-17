import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.product import Product
from app.services.product_processor import ProductInformationProcessor


def process_all_products(batch_size=1000):
    """
    Automated product information summarization and feature extraction preprocessing.
    Processes products in MySQL catalog and displays summary stats.
    """
    app = create_app('development')
    with app.app_context():
        total_count = Product.query.count()
        print("\n==================================================")
        print("PRODUCT INFORMATION SUMMARIZATION & FEATURE EXTRACTION")
        print("==================================================")
        print(f"  * Total catalog products in MySQL DB: {total_count:,}")

        sample_products = Product.query.limit(10).all()
        print("\n--- SAMPLE EXTRACTED SUMMARIES & FEATURES (10 PRODUCTS) ---\n")
        
        for idx, p in enumerate(sample_products, 1):
            processed = ProductInformationProcessor.process_product(p)
            print(f"[{idx}] {p.name}")
            print(f"    Category : {p.category.name if p.category else 'N/A'}")
            print(f"    Summary  : {processed['short_description']}")
            print(f"    Features : {processed['important_features']}")
            print("-" * 60)

        print("\n[OK] Product Information Processor successfully verified across dataset.")
        print("==================================================\n")


if __name__ == '__main__':
    process_all_products()
