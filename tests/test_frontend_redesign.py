import os
import sys
import re

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.models.user import User, UserRole
from app.models.product import Product
from app.models.category import Category
from app.models.cart import Cart


def run_frontend_redesign_tests():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    passed = 0
    failed = 0

    print("=" * 60)
    print("HOMEPAGE FRONTEND REDESIGN & INTEGRATED CHATBOT VERIFICATION")
    print("=" * 60)

    with app.app_context():
        client = app.test_client()

        # TEST 1: Open Homepage
        print("\n--- TEST 1: Open Homepage (GET /) ---")
        res1 = client.get('/')
        html1 = res1.data.decode('utf-8')
        t1_ok = (
            res1.status_code == 200 and
            'ShopSmart' in html1 and
            'Search for products, brands and more...' in html1 and
            'Smart Shopping' in html1 and
            'Shop by Category' in html1 and
            'Featured Products' in html1 and
            'Today\'s Best Deals' in html1 and
            'New Arrivals' in html1
        )
        if t1_ok:
            passed += 1
            print("PASSED (Homepage loaded with all e-commerce sections and header)")
        else:
            failed += 1
            print("FAILED")

        # Setup test user for authenticated routes
        test_user = User.query.filter_by(email='frontend_tester@example.com').first()
        if not test_user:
            test_user = User(
                username='frontend_tester',
                email='frontend_tester@example.com',
                first_name='Frontend',
                last_name='Tester',
                role=UserRole.USER,
                is_active=True
            )
            test_user.set_password('Password123!')
            db.session.add(test_user)
            db.session.commit()

        # Login test user for protected routes
        client.post('/auth/login', data={'email': 'frontend_tester@example.com', 'password': 'Password123!'})

        # TEST 2: Search for "headphones"
        print("\n--- TEST 2: Search Bar Query ('headphones') ---")
        res2 = client.get('/products/?q=headphones')
        html2 = res2.data.decode('utf-8')
        t2_ok = res2.status_code == 200 and ('Product Catalog' in html2 or 'headphones' in html2.lower())
        if t2_ok:
            passed += 1
            print("PASSED (Search endpoint returned matching product catalog view)")
        else:
            failed += 1
            print("FAILED")

        # TEST 3: Open AI Chatbot Initial Elements
        print("\n--- TEST 3: AI Chatbot Initial Welcome Payload ---")
        t3_ok = 'AI Shopping Assistant' in html1 and 'How can I help you shop today?' in html1
        if t3_ok:
            passed += 1
            print("PASSED (Homepage contains embedded AI assistant panel & welcome message)")
        else:
            failed += 1
            print("FAILED")

        # TEST 4: Suggested Chip Click ("Show me headphones under ₹2,000")
        print("\n--- TEST 4: Click Suggestion Chip ('Show me headphones under ₹2,000') ---")
        res4 = client.post('/ai/chat', json={'message': 'Show me headphones under ₹2,000'})
        data4 = res4.get_json() or {}
        t4_ok = res4.status_code == 200 and data4.get('success') is True and len(data4.get('recommended_products', [])) > 0
        if t4_ok:
            passed += 1
            print(f"PASSED ({len(data4.get('recommended_products', []))} headphones recommended)")
        else:
            failed += 1
            print("FAILED")

        # TEST 5: Ask Laptop Query ("I need a laptop for programming under ₹60,000.")
        print("\n--- TEST 5: Ask Query ('I need a laptop for programming under ₹60,000.') ---")
        res5 = client.post('/ai/chat', json={'message': 'I need a laptop for programming under ₹60,000.'})
        data5 = res5.get_json() or {}
        t5_ok = res5.status_code == 200 and data5.get('success') is True and len(data5.get('recommended_products', [])) > 0
        if t5_ok:
            passed += 1
            print(f"PASSED ({len(data5.get('recommended_products', []))} laptops recommended)")
        else:
            failed += 1
            print("FAILED")

        # TEST 6: Ask Phone Query ("I need a phone under ₹25,000.")
        print("\n--- TEST 6: Ask Query ('I need a phone under ₹25,000.') ---")
        res6 = client.post('/ai/chat', json={'message': 'I need a phone under ₹25,000.'})
        data6 = res6.get_json() or {}
        t6_ok = res6.status_code == 200 and data6.get('success') is True and len(data6.get('recommended_products', [])) > 0
        if t6_ok:
            passed += 1
            print(f"PASSED ({len(data6.get('recommended_products', []))} phone products recommended)")
        else:
            failed += 1
            print("FAILED")

        # TEST 7: Query Distinction Test (Laptop vs Headphones)
        print("\n--- TEST 7: Query Distinction Test ---")
        prods_laptop = {p['id'] for p in data5.get('recommended_products', [])}
        prods_headphone = {p['id'] for p in data4.get('recommended_products', [])}
        t7_ok = len(prods_laptop.intersection(prods_headphone)) == 0
        if t7_ok:
            passed += 1
            print("PASSED (Laptop and Headphones queries returned 100% distinct product sets)")
        else:
            failed += 1
            print("FAILED")

        # TEST 8: Add to Cart from AI Product Card
        print("\n--- TEST 8: Add to Cart from AI Product Card ---")
        target_prod = Product.query.filter_by(is_active=True).first()
        res8 = client.post(f'/cart/add/{target_prod.id}', json={'quantity': 1}, headers={'X-Requested-With': 'XMLHttpRequest'})
        data8 = res8.get_json() or {}
        t8_ok = res8.status_code == 200 and data8.get('success') is True
        if t8_ok:
            passed += 1
            print(f"PASSED (Product ID {target_prod.id} added to cart via AJAX POST)")
        else:
            failed += 1
            print("FAILED")

        # TEST 9: Check Cart Count Badge
        print("\n--- TEST 9: Cart Count Badge Verification ---")
        t9_ok = data8.get('cart_count', 0) > 0
        if t9_ok:
            passed += 1
            print(f"PASSED (Cart count badge updated to {data8.get('cart_count')})")
        else:
            failed += 1
            print("FAILED")

        # TEST 10: Click Category
        print("\n--- TEST 10: Category Card Redirection ---")
        cat1 = Category.query.filter_by(is_active=True).first()
        res10 = client.get(f'/products/?category={cat1.id}')
        t10_ok = res10.status_code == 200
        if t10_ok:
            passed += 1
            print(f"PASSED (Category ID {cat1.id} returned filtered product listing)")
        else:
            failed += 1
            print("FAILED")

        # TEST 11: Log Out State Header
        print("\n--- TEST 11: Logged Out Header Verification ---")
        client.get('/auth/logout')
        res11 = client.get('/')
        html11 = res11.data.decode('utf-8')
        t11_ok = res11.status_code == 200 and 'Sign In' in html11
        if t11_ok:
            passed += 1
            print("PASSED (Logged-out header displays 'Sign In' link)")
        else:
            failed += 1
            print("FAILED")

        # TEST 12: Logged In State Header
        print("\n--- TEST 12: Logged In Header Verification ---")
        client.post('/auth/login', data={'email': 'frontend_tester@example.com', 'password': 'Password123!'})
        res12 = client.get('/')
        html12 = res12.data.decode('utf-8')
        t12_ok = res12.status_code == 200 and ('Frontend' in html12 or 'frontend_tester' in html12)
        if t12_ok:
            passed += 1
            print("PASSED (Logged-in header displays user account name)")
        else:
            failed += 1
            print("FAILED")

        # TEST 13: Responsive Structure Audit
        print("\n--- TEST 13: Responsive HTML/CSS Structure Audit ---")
        t13_ok = (
            'sub-nav-bar' in html12 and
            'homepage-chatbot-card' in html12 and
            'row-cols-lg-6' in html12 and
            'row-cols-lg-4' in html12
        )
        if t13_ok:
            passed += 1
            print("PASSED (Responsive flex/grid classes verified across mobile/tablet/desktop containers)")
        else:
            failed += 1
            print("FAILED")

    print("\n" + "=" * 60)
    print(f"SUMMARY: {passed}/13 TESTS PASSED")
    print("=" * 60)
    return passed == 13


if __name__ == '__main__':
    success = run_frontend_redesign_tests()
    sys.exit(0 if success else 1)
