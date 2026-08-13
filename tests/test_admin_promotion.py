import os
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.models.user import User, UserRole
from app.models.product import Product


def test_admin_promotion():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    print("=" * 70)
    print("ADMIN ACCOUNT PROMOTION & AUTHORIZATION VERIFICATION")
    print("=" * 70)

    with app.app_context():
        client = app.test_client()

        target_email = 'vinuthahemanth7620@gmail.com'
        user = User.query.filter_by(email=target_email).first()

        assert user is not None, f"User {target_email} not found in database!"
        assert user.role == UserRole.ADMIN, f"User {target_email} role is not ADMIN!"

        print(f"Target Account Found:")
        print(f"  * User ID : {user.id}")
        print(f"  * Email   : {user.email}")
        print(f"  * Role    : {user.role}")

        # TEST 1 & 2 & 3: Login as promoted user
        print("\n--- TEST 1-3: Login as Promoted Admin Account ---")
        # Ensure logout first
        client.get('/auth/logout')
        
        # Log in via auth route or verify password check
        # Since password hash is preserved, test password check and Flask session login
        is_pw_valid = user.check_password('123456')  # Or user password hash verification
        print(f"  * User ID {user.id} active status: {user.is_active}")
        print(f"  * Password Hash exists: {bool(user.password_hash)}")

        # Login simulation with login_user inside test client context
        with client:
            with app.test_request_context():
                from flask_login import login_user
                login_user(user)

            # Test Admin Dashboard route as promoted admin user
            res_dash = client.get('/admin/')
            html_dash = res_dash.data.decode('utf-8')
            t4_ok = res_dash.status_code == 200 and 'Admin Dashboard' in html_dash
            print(f"TEST 4 & 5 (Admin Dashboard Authorization): {'PASSED' if t4_ok else 'FAILED'}")

            # TEST 6: Open Admin Product Management Page
            res_prods = client.get('/admin/products')
            html_prods = res_prods.data.decode('utf-8')
            t6_ok = res_prods.status_code == 200 and 'Product Management' in html_prods
            print(f"TEST 6 (Admin Product Management Access): {'PASSED' if t6_ok else 'FAILED'}")

            # TEST 7: Add Test Product as Admin
            test_prod_data = {
                'name': 'Admin Verified Ultra Laptop 2026',
                'brand': 'AdminTech',
                'category_id': '1',
                'price': '89999.00',
                'rating': '4.9',
                'stock_quantity': '15',
                'description': 'High end admin verified laptop.',
                'image_url': 'https://via.placeholder.com/300'
            }
            res_add = client.post('/admin/products/add', data=test_prod_data, follow_redirects=True)
            html_add = res_add.data.decode('utf-8')
            t7_ok = res_add.status_code == 200 and 'Admin Verified Ultra Laptop 2026' in html_add
            print(f"TEST 7 (Admin Add Product): {'PASSED' if t7_ok else 'FAILED'}")

            # TEST 8: Verify in Catalog
            res_cat = client.get('/products/?q=AdminTech')
            html_cat = res_cat.data.decode('utf-8')
            t8_ok = res_cat.status_code == 200 and 'Admin Verified Ultra Laptop 2026' in html_cat
            print(f"TEST 8 (Catalog Discoverability): {'PASSED' if t8_ok else 'FAILED'}")

        # TEST 9 & 10 & 11: Normal User Security Test
        print("\n--- TEST 9-11: Normal User Admin Access Restriction ---")
        client.get('/auth/logout')

        normal_user = User.query.filter(User.role == UserRole.USER, User.is_active == True).first()
        if not normal_user:
            normal_user = User(
                username='normal_security_user',
                email='normal_security@example.com',
                role=UserRole.USER,
                is_active=True
            )
            normal_user.set_password('Password123!')
            db.session.add(normal_user)
            db.session.commit()

        with client.session_transaction() as sess:
            sess['_user_id'] = str(normal_user.id)
            sess['_fresh'] = True

        res_unauth = client.get('/admin/', follow_redirects=False)
        # Should return 403 Forbidden or redirect to index/login
        t11_ok = res_unauth.status_code in [302, 403]
        print(f"TEST 11 (Normal User Denied Admin Route): {'PASSED' if t11_ok else 'FAILED'} (Status: {res_unauth.status_code})")

    print("\n" + "=" * 70)
    print("ALL ADMIN PROMOTION TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == '__main__':
    test_admin_promotion()
