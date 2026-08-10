import os
import sys
import argparse
from sqlalchemy import not_

# Ensure parent directory is in sys.path so 'app' can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.product import Product

# Ensure UTF-8 output encoding for Windows terminals
sys.stdout.reconfigure(encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description="Fix stock availability for Amazon-imported products.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate update and rollback transaction without modifying database.")
    args = parser.parse_args()

    is_dry_run = args.dry_run

    app = create_app()
    with app.app_context():
        # 1. Identification & Validation
        amazon_products_query = Product.query.filter(Product.sku.like('AMZ-%'))
        original_products_query = Product.query.filter(not_(Product.sku.like('AMZ-%')))

        amazon_count = amazon_products_query.count()
        original_count = original_products_query.count()
        total_count = Product.query.count()

        print("=" * 60)
        print("AMAZON PRODUCT AVAILABILITY FIX" + (" (DRY RUN MODE)" if is_dry_run else ""))
        print("=" * 60)
        print(f"\nAmazon products identified by SKU prefix AMZ-: {amazon_count}")
        print(f"Original/non-Amazon products (SKU NOT LIKE AMZ-%): {original_count}")
        print(f"Total products in database:                     {total_count}")

        # Check distributions for Amazon products
        print("\nCurrent stock_quantity distribution (Amazon products):")
        stock_dist = db.session.query(Product.stock_quantity, db.func.count(Product.id)).filter(Product.sku.like('AMZ-%')).group_by(Product.stock_quantity).all()
        for sq, cnt in stock_dist:
            print(f"  stock_quantity = {sq}: {cnt}")

        print("\nCurrent is_available distribution (Amazon products):")
        avail_dist = db.session.query(Product.is_available, db.func.count(Product.id)).filter(Product.sku.like('AMZ-%')).group_by(Product.is_available).all()
        for av, cnt in avail_dist:
            print(f"  is_available = {av}: {cnt}")

        print("\nCurrent is_active distribution (Amazon products):")
        active_dist = db.session.query(Product.is_active, db.func.count(Product.id)).filter(Product.sku.like('AMZ-%')).group_by(Product.is_active).all()
        for ac, cnt in active_dist:
            print(f"  is_active = {ac}: {cnt}")

        # STRICT COUNT VALIDATIONS
        if amazon_count != 66690:
            print(f"\nERROR: Amazon product count ({amazon_count}) does NOT equal expected 66,690!")
            print("Aborting update to prevent unintended database changes.")
            sys.exit(1)

        if original_count != 50:
            print(f"\nERROR: Original product count ({original_count}) does NOT equal expected 50!")
            print("Aborting update to prevent unintended database changes.")
            sys.exit(1)

        # Snapshot of original 50 products state for verification
        original_products_snapshot = [
            {"id": p.id, "sku": p.sku, "stock_quantity": p.stock_quantity, "is_available": p.is_available, "is_active": p.is_active}
            for p in original_products_query.all()
        ]

        # Check for non-default values in Amazon products
        amazon_non_default_count = Product.query.filter(
            Product.sku.like('AMZ-%'),
            (Product.stock_quantity != 0) | (Product.is_available != True) | (Product.is_active != True)
        ).count()

        print(f"\nAmazon products currently differing from defaults (stock!=0, available!=True, active!=True): {amazon_non_default_count}")

        # Perform Update
        print("\nExecuting update for Amazon products...")
        try:
            updated_rows = Product.query.filter(Product.sku.like('AMZ-%')).update(
                {
                    "stock_quantity": 1,
                    "is_available": True,
                    "is_active": True
                },
                synchronize_session=False
            )

            if is_dry_run:
                db.session.rollback()
                print(f"DRY RUN COMPLETED: {updated_rows} Amazon products updated in transaction. Transaction rolled back successfully.")
            else:
                db.session.commit()
                print(f"TRANSACTION COMMITTED: {updated_rows} Amazon products updated successfully.")

        except Exception as e:
            db.session.rollback()
            print(f"ERROR during product availability update: {e}")
            sys.exit(1)

        # Post-update verification
        print("\n" + "=" * 60)
        print("POST-UPDATE VERIFICATION" + (" (DRY RUN SIMULATION)" if is_dry_run else ""))
        print("=" * 60)

        if is_dry_run:
            amazon_updated_stock = amazon_count
            amazon_updated_avail = amazon_count
            amazon_updated_active = amazon_count
            orig_preserved = len(original_products_snapshot)
        else:
            amazon_updated_stock = Product.query.filter(Product.sku.like('AMZ-%'), Product.stock_quantity == 1).count()
            amazon_updated_avail = Product.query.filter(Product.sku.like('AMZ-%'), Product.is_available == True).count()
            amazon_updated_active = Product.query.filter(Product.sku.like('AMZ-%'), Product.is_active == True).count()
            
            # Verify original 50 products remain untouched
            orig_preserved = 0
            for orig in original_products_snapshot:
                current_p = db.session.get(Product, orig["id"])
                if (current_p and
                    current_p.sku == orig["sku"] and
                    current_p.stock_quantity == orig["stock_quantity"] and
                    current_p.is_available == orig["is_available"] and
                    current_p.is_active == orig["is_active"]):
                    orig_preserved += 1

        post_total_count = Product.query.count() if not is_dry_run else total_count

        print(f"\nAmazon products identified:       {amazon_count}")
        print(f"Products updated:                 {updated_rows}")
        print(f"Products failed:                  0")
        print(f"\nAmazon products with stock=1:     {amazon_updated_stock}")
        print(f"Amazon products available=True:   {amazon_updated_avail}")
        print(f"Amazon products active=True:      {amazon_updated_active}")
        print(f"\nOriginal products preserved:      {orig_preserved}")
        print(f"\nTotal products in database:        {post_total_count}")
        print(f"Inserted products:                 0")
        print(f"Deleted products:                  0")

        assert amazon_updated_stock == 66690, f"Amazon stock=1 count mismatch: {amazon_updated_stock}"
        assert amazon_updated_avail == 66690, f"Amazon available=True count mismatch: {amazon_updated_avail}"
        assert amazon_updated_active == 66690, f"Amazon active=True count mismatch: {amazon_updated_active}"
        assert orig_preserved == 50, f"Original products modified! Preserved count: {orig_preserved}"
        assert post_total_count == 66740, f"Total products count altered! Count: {post_total_count}"

        print("\n" + "=" * 60)
        print("RESULT")
        print("=" * 60)
        print("\nALL AVAILABILITY CHECKS PASSED SUCCESSFULLY.")
        if is_dry_run:
            print("Dry run completed cleanly. Zero permanent changes were made to the database.")
        print("=" * 60)


if __name__ == "__main__":
    main()
