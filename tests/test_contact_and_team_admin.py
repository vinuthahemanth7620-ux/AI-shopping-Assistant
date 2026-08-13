import os
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.models.user import User, UserRole
from app.models.contact_message import ContactMessage


def run_contact_and_team_admin_tests():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    print("=" * 70)
    print("CONTACT US, TEAM CARDS & ADMIN AUTHORIZATION TEST SUITE")
    print("=" * 70)

    passed = 0
    failed = 0

    with app.app_context():
        # Ensure database tables exist (e.g. contact_messages)
        db.create_all()

        client = app.test_client()

        # ---------------------------------------------------------------------
        # TEST 1 & 2: HOMEPAGE & CONTACT PAGE LOADING
        # ---------------------------------------------------------------------
        print("\n--- TEST GROUP 1: PAGE LOADING ---")
        res_home = client.get('/')
        t1_ok = res_home.status_code == 200
        print(f"1. Homepage Load: {'PASSED' if t1_ok else 'FAILED'}")
        if t1_ok: passed += 1
        else: failed += 1

        res_contact = client.get('/contact')
        html_contact = res_contact.data.decode('utf-8')
        t2_ok = res_contact.status_code == 200 and 'Contact Us' in html_contact
        print(f"2. Contact Us Page Load: {'PASSED' if t2_ok else 'FAILED'}")
        if t2_ok: passed += 1
        else: failed += 1

        # ---------------------------------------------------------------------
        # TEST 3: TEAM MEMBERS & CONTACT DETAILS IN HTML
        # ---------------------------------------------------------------------
        print("\n--- TEST GROUP 2: TEAM DETAILS & LINKS ---")
        v_ok = 'VINUTHA' in html_contact and 'AI & Python Backend Developer' in html_contact and 'vinuthahemanth7620@gmail.com' in html_contact and '7259886752' in html_contact
        t_ok = 'THANUSHREE P.H' in html_contact and 'Frontend & UI/UX Developer' in html_contact and 'thanushreeph14@gmail.com' in html_contact and '6363507368' in html_contact
        links_ok = 'github.com/vinuthahemanth7620' in html_contact and 'github.com/thanushreeph14-del' in html_contact and 'linkedin.com/in/vinutha467304310' in html_contact and 'linkedin.com/in/thanushree-ph' in html_contact
        
        t3_ok = v_ok and t_ok and links_ok
        print(f"3. Team Cards & Clickable Social/Contact Links: {'PASSED' if t3_ok else 'FAILED'}")
        if t3_ok: passed += 1
        else: failed += 1

        # ---------------------------------------------------------------------
        # TEST 4: CONTACT FORM VALIDATION & SUBMISSION
        # ---------------------------------------------------------------------
        print("\n--- TEST GROUP 3: CONTACT FORM SUBMISSION ---")
        # Empty field test
        res_empty = client.post('/contact', data={'name': '', 'email': 'test@example.com', 'subject': 'Sub', 'message': 'Msg'})
        t4a_ok = 'Please enter your full name.' in res_empty.data.decode('utf-8')
        print(f"4A. Empty Name Validation: {'PASSED' if t4a_ok else 'FAILED'}")

        # Invalid email test
        res_invalid_email = client.post('/contact', data={'name': 'Tester', 'email': 'invalid-email', 'subject': 'Sub', 'message': 'Msg'})
        t4b_ok = 'Please enter a valid email address.' in res_invalid_email.data.decode('utf-8')
        print(f"4B. Invalid Email Validation: {'PASSED' if t4b_ok else 'FAILED'}")

        # Successful submission
        res_sub = client.post('/contact', data={
            'name': 'Customer Support Tester',
            'email': 'customer@example.com',
            'subject': 'Inquiry regarding AI Assistant',
            'message': 'Great application! How does recommendation scoring work?'
        }, follow_redirects=True)
        t4c_ok = res_sub.status_code == 200 and 'Thank you for contacting us!' in res_sub.data.decode('utf-8')
        print(f"4C. Successful Form Submission: {'PASSED' if t4c_ok else 'FAILED'}")

        # DB persistence check
        saved_msg = ContactMessage.query.filter_by(email='customer@example.com').first()
        t4d_ok = saved_msg is not None and saved_msg.subject == 'Inquiry regarding AI Assistant'
        print(f"4D. Contact Message DB Persistence: {'PASSED' if t4d_ok else 'FAILED'}")

        if t4a_ok and t4b_ok and t4c_ok and t4d_ok: passed += 1
        else: failed += 1

        # ---------------------------------------------------------------------
        # TEST 5: ADMIN AUTHORIZATION FOR VINUTHA & THANUSHREE P.H
        # ---------------------------------------------------------------------
        print("\n--- TEST GROUP 4: ADMIN AUTHORIZATION FOR TEAM ACCOUNTS ---")
        u_v = User.query.filter_by(email='vinuthahemanth7620@gmail.com').first()
        u_t = User.query.filter_by(email='thanushreeph14@gmail.com').first()

        assert u_v is not None, "User vinuthahemanth7620@gmail.com not found!"
        assert u_t is not None, "User thanushreeph14@gmail.com not found!"

        t5a_ok = (u_v.role == UserRole.ADMIN or str(u_v.role).lower() == 'admin')
        t5b_ok = (u_t.role == UserRole.ADMIN or str(u_t.role).lower() == 'admin')
        print(f"5A. VINUTHA Admin Role in DB: {'PASSED' if t5a_ok else 'FAILED'}")
        print(f"5B. THANUSHREE P.H Admin Role in DB: {'PASSED' if t5b_ok else 'FAILED'}")

        # Test Vinutha admin access
        with client:
            with app.test_request_context():
                from flask_login import login_user
                login_user(u_v)
            res_v_dash = client.get('/admin/')
            res_v_msg = client.get('/admin/messages')
            t5c_ok = res_v_dash.status_code == 200 and res_v_msg.status_code == 200
            print(f"5C. VINUTHA Admin Dashboard & Contact Messages Access: {'PASSED' if t5c_ok else 'FAILED'}")

        # Test Thanushree admin access
        with client:
            with app.test_request_context():
                from flask_login import login_user
                login_user(u_t)
            res_t_dash = client.get('/admin/')
            res_t_msg = client.get('/admin/messages')
            t5d_ok = res_t_dash.status_code == 200 and res_t_msg.status_code == 200
            print(f"5D. THANUSHREE P.H Admin Dashboard & Contact Messages Access: {'PASSED' if t5d_ok else 'FAILED'}")

        if t5a_ok and t5b_ok and t5c_ok and t5d_ok: passed += 1
        else: failed += 1

        # ---------------------------------------------------------------------
        # TEST 6: NORMAL USER RESTRICTION & CORE MODULE STABILITY
        # ---------------------------------------------------------------------
        print("\n--- TEST GROUP 5: SYSTEM SECURITY & STABILITY ---")
        normal_u = User.query.filter(User.email.notin_(['vinuthahemanth7620@gmail.com', 'thanushreeph14@gmail.com'])).first()
        with client:
            if normal_u:
                with app.test_request_context():
                    from flask_login import login_user
                    login_user(normal_u)
            res_norm_dash = client.get('/admin/', follow_redirects=False)
            res_norm_msg = client.get('/admin/messages', follow_redirects=False)
            t6a_ok = res_norm_dash.status_code in [302, 403] and res_norm_msg.status_code in [302, 403]
            print(f"6A. Normal User Denied Admin Routes: {'PASSED' if t6a_ok else 'FAILED'}")

        res_about = client.get('/about')
        res_prods = client.get('/products/')
        res_cart = client.get('/cart/')
        res_wish = client.get('/wishlist/')
        res_ai = client.get('/ai/')

        t6b_ok = res_about.status_code == 200 and res_prods.status_code == 200 and res_cart.status_code == 200 and res_wish.status_code == 200 and res_ai.status_code == 200
        print(f"6B. Core Application Modules Operational (About, Catalog, Cart, Wishlist, AI): {'PASSED' if t6b_ok else 'FAILED'}")

        if t6a_ok and t6b_ok: passed += 1
        else: failed += 1

        # ---------------------------------------------------------------------
        # SUMMARY
        # ---------------------------------------------------------------------
        print("\n" + "=" * 70)
        print(f"CONTACT & TEAM ADMIN AUDIT SUMMARY: {passed} PASSED / {failed} FAILED")
        print("=" * 70)

        return failed == 0


if __name__ == '__main__':
    run_contact_and_team_admin_tests()
