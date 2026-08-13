import os
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.models.user import User, UserRole
from app.models.product import Product
from app.models.category import Category
from app.models.cart import Cart
from app.models.wishlist import Wishlist
from app.models.order import Order, OrderStatus
from app.models.chat_history import ChatHistory


def run_audit_and_bugfix_tests():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    passed = 0
    failed = 0

    print("=" * 70)
    print("AI SHOPPING ASSISTANT — COMPLETE FUNCTIONAL AUDIT & BUGFIX TEST SUITE")
    print("=" * 70)

    with app.app_context():
        # Ensure database tables exist
        db.create_all()
        client = app.test_client()

        # Setup test user
        test_user = User.query.filter_by(email='audit_tester@example.com').first()
        if not test_user:
            test_user = User(
                username='audit_tester',
                email='audit_tester@example.com',
                first_name='Audit',
                last_name='Tester',
                role=UserRole.USER,
                is_active=True
            )
            test_user.set_password('Password123!')
            db.session.add(test_user)
            db.session.commit()

        # Setup admin user
        admin_user = User.query.filter_by(email='admin_tester@example.com').first()
        if not admin_user:
            admin_user = User(
                username='admin_tester',
                email='admin_tester@example.com',
                first_name='Admin',
                last_name='Tester',
                role=UserRole.ADMIN,
                is_active=True
            )
            admin_user.set_password('AdminPass123!')
            db.session.add(admin_user)
            db.session.commit()

        # Log in test user
        client.post('/auth/login', data={'email': 'audit_tester@example.com', 'password': 'Password123!'})

        # ---------------------------------------------------------------------
        # TEST GROUP 1: WISHLIST MODULE END-TO-END
        # ---------------------------------------------------------------------
        print("\n--- TEST GROUP 1: WISHLIST MODULE END-TO-END ---")
        p1 = Product.query.filter_by(is_active=True).first()

        # 1A: Toggle Add
        res1a = client.post(f'/wishlist/toggle/{p1.id}', headers={'X-Requested-With': 'XMLHttpRequest'})
        data1a = res1a.get_json() or {}
        t1a_ok = res1a.status_code == 200 and data1a.get('is_wishlisted') is True and data1a.get('wishlist_count', 0) >= 1
        print(f"Wishlist Toggle Add: {'PASSED' if t1a_ok else 'FAILED'}")
        if t1a_ok: passed += 1
        else: failed += 1

        # 1B: View Wishlist Page
        res1b = client.get('/wishlist/')
        html1b = res1b.data.decode('utf-8')
        t1b_ok = res1b.status_code == 200 and 'My Wishlist' in html1b and p1.name[:15] in html1b
        print(f"View Wishlist Page: {'PASSED' if t1b_ok else 'FAILED'}")
        if t1b_ok: passed += 1
        else: failed += 1

        # 1C: Wishlist Status API
        res1c = client.get('/wishlist/status')
        data1c = res1c.get_json() or {}
        t1c_ok = res1c.status_code == 200 and p1.id in data1c.get('wishlist_ids', [])
        print(f"Wishlist Status API: {'PASSED' if t1c_ok else 'FAILED'}")
        if t1c_ok: passed += 1
        else: failed += 1

        # 1D: Toggle Remove
        res1d = client.post(f'/wishlist/toggle/{p1.id}', headers={'X-Requested-With': 'XMLHttpRequest'})
        data1d = res1d.get_json() or {}
        t1d_ok = res1d.status_code == 200 and data1d.get('is_wishlisted') is False
        print(f"Wishlist Toggle Remove: {'PASSED' if t1d_ok else 'FAILED'}")
        if t1d_ok: passed += 1
        else: failed += 1

        # ---------------------------------------------------------------------
        # TEST GROUP 2: AI CHATBOT 12-QUERY TEST MATRIX (NO AIRPODS BUG)
        # ---------------------------------------------------------------------
        print("\n--- TEST GROUP 2: AI CHATBOT 12-QUERY MATRIX ---")

        matrix_queries = [
            ("Show me a laptop.", "laptop"),
            ("Show me a phone.", "phone"),
            ("I need wireless earbuds.", "earbuds"),
            ("Show me a camera.", "camera"),
            ("I need running shoes.", "shoes"),
            ("Show me a smartwatch.", "watch"),
            ("I need a backpack for college.", "college"),
            ("Show me a shirt.", "shirt"),
            ("I need something for my kitchen.", "kitchen"),
            ("I need a laptop under ₹60000.", "laptop_budget"),
            ("Show me highly rated phones.", "phone_rated"),
            ("Find something under ₹5000.", "budget_general")
        ]

        matrix_passed = True
        for q_text, q_id in matrix_queries:
            res_q = client.post('/ai/chat', json={'message': q_text})
            data_q = res_q.get_json() or {}
            prods = data_q.get('recommended_products', [])
            
            # Check for earphone bug (non-headphone queries returning earphones)
            has_earphone_bug = False
            if q_id not in ['earbuds']:
                for prod in prods:
                    p_name_l = prod['name'].lower()
                    if any(bad in p_name_l for bad in ['airpods', 'earbud', 'earphone', 'headphone']):
                        has_earphone_bug = True
                        break

            is_ok = res_q.status_code == 200 and data_q.get('success') is True and not has_earphone_bug
            print(f"  * Query '{q_text}': {'PASSED' if is_ok else 'FAILED'} (Returned {len(prods)} products, Earphone Bug: {has_earphone_bug})")
            if not is_ok:
                matrix_passed = False

        print(f"12-Query AI Matrix: {'PASSED' if matrix_passed else 'FAILED'}")
        if matrix_passed: passed += 1
        else: failed += 1

        # ---------------------------------------------------------------------
        # TEST GROUP 3: CONSECUTIVE QUERY DISTINCTION TEST
        # ---------------------------------------------------------------------
        print("\n--- TEST GROUP 3: CONSECUTIVE QUERY DISTINCTION ---")
        ChatHistory.query.filter_by(user_id=test_user.id).delete()
        db.session.commit()

        res_laptop = client.post('/ai/chat', json={'message': 'Show me laptops'})
        res_phone = client.post('/ai/chat', json={'message': 'Show me smartphones'})
        
        d_laptop = res_laptop.get_json() or {}
        d_phone = res_phone.get_json() or {}

        ids_laptop = {p['id'] for p in d_laptop.get('recommended_products', [])}
        ids_phone = {p['id'] for p in d_phone.get('recommended_products', [])}

        t3_ok = len(ids_laptop) > 0 and len(ids_phone) > 0 and len(ids_laptop.intersection(ids_phone)) == 0
        print(f"Consecutive Query Distinction: {'PASSED' if t3_ok else 'FAILED'}")
        if t3_ok: passed += 1
        else: failed += 1

        # ---------------------------------------------------------------------
        # TEST GROUP 4: CART & CHECKOUT END-TO-END
        # ---------------------------------------------------------------------
        print("\n--- TEST GROUP 4: CART & CHECKOUT END-TO-END ---")
        
        # 4A: Add to Cart
        res4a = client.post(f'/cart/add/{p1.id}', json={'quantity': 1}, headers={'X-Requested-With': 'XMLHttpRequest'})
        data4a = res4a.get_json() or {}
        t4a_ok = res4a.status_code == 200 and data4a.get('success') is True
        print(f"Add to Cart: {'PASSED' if t4a_ok else 'FAILED'}")
        if t4a_ok: passed += 1
        else: failed += 1

        # 4B: View Checkout Page
        res4b = client.get('/orders/checkout')
        html4b = res4b.data.decode('utf-8')
        t4b_ok = res4b.status_code == 200 and 'Checkout' in html4b and 'Order Summary' in html4b
        print(f"View Checkout Page: {'PASSED' if t4b_ok else 'FAILED'}")
        if t4b_ok: passed += 1
        else: failed += 1

        # 4C: Place Order
        checkout_payload = {
            'full_name': 'Audit Tester',
            'email': 'audit_tester@example.com',
            'phone': '9876543210',
            'shipping_address': '123 Test Street',
            'city': 'Bangalore',
            'postal_code': '560001',
            'payment_method': 'Cash on Delivery'
        }
        res4c = client.post('/orders/checkout', data=checkout_payload, follow_redirects=True)
        html4c = res4c.data.decode('utf-8')
        t4c_ok = res4c.status_code == 200 and ('Order Details' in html4c or 'ORD-' in html4c)
        print(f"Place Order: {'PASSED' if t4c_ok else 'FAILED'}")
        if t4c_ok: passed += 1
        else: failed += 1

        # 4D: View Orders History Page
        res4d = client.get('/orders/')
        html4d = res4d.data.decode('utf-8')
        t4d_ok = res4d.status_code == 200 and 'My Orders' in html4d and 'ORD-' in html4d
        print(f"View Orders History Page: {'PASSED' if t4d_ok else 'FAILED'}")
        if t4d_ok: passed += 1
        else: failed += 1

        # ---------------------------------------------------------------------
        # TEST GROUP 5: COMPARE SPECS, PLANNER, PROFILE MODULES
        # ---------------------------------------------------------------------
        print("\n--- TEST GROUP 5: COMPARE, PLANNER, PROFILE ---")

        # 5A: Compare Specs Page
        res5a = client.get('/compare/')
        html5a = res5a.data.decode('utf-8')
        t5a_ok = res5a.status_code == 200 and 'Product Comparison' in html5a
        print(f"Compare Specs View: {'PASSED' if t5a_ok else 'FAILED'}")
        if t5a_ok: passed += 1
        else: failed += 1

        # 5B: Shopping Planner Add & View
        res5b1 = client.post('/planner/', data={'action': 'add', 'title': 'Test Headphone Plan', 'target_budget': '2500'}, follow_redirects=True)
        html5b = res5b1.data.decode('utf-8')
        t5b_ok = res5b1.status_code == 200 and 'Test Headphone Plan' in html5b
        print(f"Shopping Planner Add & View: {'PASSED' if t5b_ok else 'FAILED'}")
        if t5b_ok: passed += 1
        else: failed += 1

        # 5C: User Profile View & Update
        res5c = client.post('/profile/', data={'first_name': 'AuditUpdated', 'last_name': 'Tester'}, follow_redirects=True)
        html5c = res5c.data.decode('utf-8')
        t5c_ok = res5c.status_code == 200 and 'AuditUpdated' in html5c
        print(f"User Profile View & Update: {'PASSED' if t5c_ok else 'FAILED'}")
        if t5c_ok: passed += 1
        else: failed += 1

        # ---------------------------------------------------------------------
        # TEST GROUP 6: ADMIN PRODUCT CREATION & AI DISCOVERABILITY
        # ---------------------------------------------------------------------
        print("\n--- TEST GROUP 6: ADMIN PRODUCT CREATION & AI DISCOVERABILITY ---")
        client.get('/auth/logout')
        client.post('/auth/login', data={'email': 'admin_tester@example.com', 'password': 'AdminPass123!'})

        # 6A: Admin Add Product
        new_prod_data = {
            'name': 'Quantum Ultra Book X15 Laptop',
            'brand': 'Quantum',
            'category_id': '1',
            'price': '75000.00',
            'rating': '4.8',
            'stock_quantity': '10',
            'description': 'High performance laptop for gaming and programming.',
            'image_url': 'https://via.placeholder.com/300x300.png?text=Quantum+Laptop'
        }
        res6a = client.post('/admin/products/add', data=new_prod_data, follow_redirects=True)
        html6a = res6a.data.decode('utf-8')
        t6a_ok = res6a.status_code == 200 and 'Quantum Ultra Book X15 Laptop' in html6a
        print(f"Admin Add Product: {'PASSED' if t6a_ok else 'FAILED'}")
        if t6a_ok: passed += 1
        else: failed += 1

        # 6B: Search for Admin Added Product
        res6b = client.get('/products/?q=Quantum')
        html6b = res6b.data.decode('utf-8')
        t6b_ok = res6b.status_code == 200 and 'Quantum Ultra Book X15 Laptop' in html6b
        print(f"Search Admin Added Product: {'PASSED' if t6b_ok else 'FAILED'}")
        if t6b_ok: passed += 1
        else: failed += 1

        # 6C: AI Discoverability of Admin Added Product
        res6c = client.post('/ai/chat', json={'message': 'Quantum laptop'})
        data6c = res6c.get_json() or {}
        prods6c = data6c.get('recommended_products', [])
        found_admin_prod = any(p['name'] == 'Quantum Ultra Book X15 Laptop' for p in prods6c)
        t6c_ok = res6c.status_code == 200 and found_admin_prod
        print(f"AI Discoverability of Admin Product: {'PASSED' if t6c_ok else 'FAILED'}")
        if t6c_ok: passed += 1
        else: failed += 1

        # 6D: Admin Orders Listing
        res6d = client.get('/admin/orders')
        html6d = res6d.data.decode('utf-8')
        t6d_ok = res6d.status_code == 200 and 'Customer Orders Management' in html6d
        print(f"Admin Orders Listing: {'PASSED' if t6d_ok else 'FAILED'}")
        if t6d_ok: passed += 1
        else: failed += 1

    print("\n" + "=" * 70)
    print(f"AUDIT SUMMARY: {passed} PASSED / {failed} FAILED (TOTAL {passed + failed} TEST SUITES)")
    print("=" * 70)
    return failed == 0


if __name__ == '__main__':
    success = run_audit_and_bugfix_tests()
    sys.exit(0 if success else 1)
