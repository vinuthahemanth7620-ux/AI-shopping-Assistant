import os
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.services.ai_service import AIService
from app.recommendation.engine import RecommendationEngine
from app.recommendation.parser import RequirementParser
from app.models.user import User, UserRole
from app.models.chat_history import ChatHistory


def test_ai_assistant_accuracy():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    passed = 0
    failed = 0

    print("=" * 80)
    print("AI SHOPPING ASSISTANT - CATEGORY CLASSIFICATION & ACCURACY SUITE")
    print("=" * 80)

    with app.app_context():
        client = app.test_client()

        # Setup test user
        test_user = User.query.filter_by(email='ai_accuracy_tester@example.com').first()
        if not test_user:
            test_user = User(
                username='ai_accuracy_tester',
                email='ai_accuracy_tester@example.com',
                first_name='AI',
                last_name='Tester',
                role=UserRole.USER,
                is_active=True
            )
            test_user.set_password('Password123!')
            db.session.add(test_user)
            db.session.commit()

        # Noise words that MUST NEVER be returned for beauty/makeup/cosmetics queries
        unrelated_noise = ['refrigerator', 'mini fridge', 'stove', 'cooktop', 'microwave', 'oven', 'vanity table', 'screwdriver', 'flag', 'bed frame', 'volleyball', 'vacuum', 'dishwasher', 'laptop', 'headphone', 'phone', 'tumbler', 'coffee mug', 'straw cup']

        # ---------------------------------------------------------------------
        # TEST 1: "makeup items"
        # ---------------------------------------------------------------------
        print("\n--- TEST 1: Query 'makeup items' ---")
        res1 = client.post('/ai/chat', json={'message': 'makeup items'})
        data1 = res1.get_json() or {}
        prods1 = data1.get('recommended_products', [])
        text1 = data1.get('ai_response', '')
        t1_has_noise = any(any(nw in p['name'].lower() for nw in unrelated_noise) for p in prods1)
        t1_ok = res1.status_code == 200 and len(prods1) > 0 and not t1_has_noise and '2,000' not in text1
        print(f"1. 'makeup items' Returns Beauty/Cosmetics Products Only: {'PASSED' if t1_ok else 'FAILED'}")
        if t1_ok:
            passed += 1
            print(f"   Returned: {[p['name'][:50] for p in prods1]}")
        else:
            failed += 1
            print(f"   FAILED text: {text1!r} | Returned: {[p['name'] for p in prods1]}")

        # ---------------------------------------------------------------------
        # TEST 2: "Show me some cosmetics"
        # ---------------------------------------------------------------------
        print("\n--- TEST 2: Query 'Show me some cosmetics' ---")
        res2 = client.post('/ai/chat', json={'message': 'Show me some cosmetics'})
        data2 = res2.get_json() or {}
        prods2 = data2.get('recommended_products', [])
        t2_has_noise = any(any(nw in p['name'].lower() for nw in unrelated_noise) for p in prods2)
        t2_ok = res2.status_code == 200 and len(prods2) > 0 and not t2_has_noise
        print(f"2. 'Show me some cosmetics' Query: {'PASSED' if t2_ok else 'FAILED'}")
        if t2_ok: passed += 1
        else: failed += 1

        # ---------------------------------------------------------------------
        # TEST 3: "I need products for doing makeup"
        # ---------------------------------------------------------------------
        print("\n--- TEST 3: Query 'I need products for doing makeup' ---")
        res3 = client.post('/ai/chat', json={'message': 'I need products for doing makeup'})
        data3 = res3.get_json() or {}
        prods3 = data3.get('recommended_products', [])
        t3_has_noise = any(any(nw in p['name'].lower() for nw in unrelated_noise) for p in prods3)
        t3_ok = res3.status_code == 200 and len(prods3) > 0 and not t3_has_noise
        print(f"3. 'I need products for doing makeup' Query: {'PASSED' if t3_ok else 'FAILED'}")
        if t3_ok: passed += 1
        else: failed += 1

        # ---------------------------------------------------------------------
        # TEST 4: "Show me lipstick"
        # ---------------------------------------------------------------------
        print("\n--- TEST 4: Query 'Show me lipstick' ---")
        res4 = client.post('/ai/chat', json={'message': 'Show me lipstick'})
        data4 = res4.get_json() or {}
        prods4 = data4.get('recommended_products', [])
        t4_has_noise = any(any(nw in p['name'].lower() for nw in unrelated_noise) for p in prods4)
        t4_ok = res4.status_code == 200 and len(prods4) > 0 and not t4_has_noise
        print(f"4. 'Show me lipstick' Query: {'PASSED' if t4_ok else 'FAILED'}")
        if t4_ok: passed += 1
        else: failed += 1

        # ---------------------------------------------------------------------
        # TEST 5: "I need an induction stove"
        # ---------------------------------------------------------------------
        print("\n--- TEST 5: Query 'I need an induction stove' ---")
        res5 = client.post('/ai/chat', json={'message': 'I need an induction stove'})
        data5 = res5.get_json() or {}
        prods5 = data5.get('recommended_products', [])
        cooktop_bad = ['screwdriver', 'lamp', 'vanity', 'knob', 'cover', 'repellent', 'cat', 'hood light', 'fire pit']
        t5_noise = any(any(bw in p['name'].lower() for bw in cooktop_bad) for p in prods5)
        t5_ok = res5.status_code == 200 and len(prods5) > 0 and not t5_noise
        print(f"5. 'I need an induction stove' Query: {'PASSED' if t5_ok else 'FAILED'}")
        if t5_ok: passed += 1
        else: failed += 1

        # ---------------------------------------------------------------------
        # TEST 6: "Show me headphones"
        # ---------------------------------------------------------------------
        print("\n--- TEST 6: Query 'Show me headphones' ---")
        res6 = client.post('/ai/chat', json={'message': 'Show me headphones'})
        data6 = res6.get_json() or {}
        prods6 = data6.get('recommended_products', [])
        t6_is_headphones = all(any(hk in p['name'].lower() for hk in ['headphone', 'headphones', 'earphone', 'earphones', 'earbud', 'earbuds', 'headset', 'airpods']) for p in prods6)
        t6_ok = res6.status_code == 200 and len(prods6) > 0 and t6_is_headphones
        print(f"6. 'Show me headphones' Query: {'PASSED' if t6_ok else 'FAILED'}")
        if t6_ok: passed += 1
        else: failed += 1

        # ---------------------------------------------------------------------
        # TEST 7: "I need a laptop"
        # ---------------------------------------------------------------------
        print("\n--- TEST 7: Query 'I need a laptop' ---")
        res7 = client.post('/ai/chat', json={'message': 'I need a laptop'})
        data7 = res7.get_json() or {}
        prods7 = data7.get('recommended_products', [])
        text7 = data7.get('ai_response', '')
        t7_no_fake_budget = '2,000' not in text7
        t7_is_laptops = all(any(lk in p['name'].lower() for lk in ['laptop', 'notebook', 'macbook', 'aspire', 'ideapad', 'thinkpad', 'pavilion', 'legion', 'zenbook', 'vivobook', 'inspiron', 'latitude', 'xps', 'chromebook', 'convertible']) for p in prods7)
        t7_ok = res7.status_code == 200 and len(prods7) > 0 and t7_no_fake_budget and t7_is_laptops
        print(f"7. 'I need a laptop' Query Returns Laptops without Invented Budget: {'PASSED' if t7_ok else 'FAILED'}")
        if t7_ok: passed += 1
        else: failed += 1

        # ---------------------------------------------------------------------
        # TEST 8: "Suggest running shoes"
        # ---------------------------------------------------------------------
        print("\n--- TEST 8: Query 'Suggest running shoes' ---")
        res8 = client.post('/ai/chat', json={'message': 'Suggest running shoes'})
        data8 = res8.get_json() or {}
        prods8 = data8.get('recommended_products', [])
        t8_ok = res8.status_code == 200 and len(prods8) > 0
        print(f"8. 'Suggest running shoes' Query: {'PASSED' if t8_ok else 'FAILED'}")
        if t8_ok: passed += 1
        else: failed += 1

        # ---------------------------------------------------------------------
        # TEST 9: "Show me skincare products"
        # ---------------------------------------------------------------------
        print("\n--- TEST 9: Query 'Show me skincare products' ---")
        res9 = client.post('/ai/chat', json={'message': 'Show me skincare products'})
        data9 = res9.get_json() or {}
        prods9 = data9.get('recommended_products', [])
        t9_has_noise = any(any(nw in p['name'].lower() for nw in unrelated_noise) for p in prods9)
        t9_ok = res9.status_code == 200 and len(prods9) > 0 and not t9_has_noise
        print(f"9. 'Show me skincare products' Query: {'PASSED' if t9_ok else 'FAILED'}")
        if t9_ok: passed += 1
        else: failed += 1

        # ---------------------------------------------------------------------
        # TEST 10: "Find kitchen appliances"
        # ---------------------------------------------------------------------
        print("\n--- TEST 10: Query 'Find kitchen appliances' ---")
        res10 = client.post('/ai/chat', json={'message': 'Find kitchen appliances'})
        data10 = res10.get_json() or {}
        prods10 = data10.get('recommended_products', [])
        t10_ok = res10.status_code == 200 and len(prods10) > 0
        print(f"10. 'Find kitchen appliances' Broad Query: {'PASSED' if t10_ok else 'FAILED'}")
        if t10_ok: passed += 1
        else: failed += 1

        # ---------------------------------------------------------------------
        # TEST 11: "Find birthday gifts"
        # ---------------------------------------------------------------------
        print("\n--- TEST 11: Query 'Find birthday gifts' ---")
        res11 = client.post('/ai/chat', json={'message': 'Find birthday gifts'})
        data11 = res11.get_json() or {}
        text11 = data11.get('ai_response', '')
        prods11 = data11.get('recommended_products', [])
        t11_no_fake_budget = '2,000' not in text11
        t11_ok = res11.status_code == 200 and len(prods11) > 0 and t11_no_fake_budget
        print(f"11. 'Find birthday gifts' Query: {'PASSED' if t11_ok else 'FAILED'}")
        if t11_ok: passed += 1
        else: failed += 1

        # ---------------------------------------------------------------------
        # SUMMARY
        # ---------------------------------------------------------------------
        print("\n" + "=" * 80)
        print(f"AI CATEGORY & INTENT ACCURACY SUMMARY: {passed} PASSED / {failed} FAILED")
        print("=" * 80)

        return failed == 0


if __name__ == '__main__':
    test_ai_assistant_accuracy()
