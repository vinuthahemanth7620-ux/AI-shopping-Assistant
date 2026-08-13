import os
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.models.user import User, UserRole
from app.models.contact_message import ContactMessage
from app.models.team_member import TeamMember


def test_team_security_isolation():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    print("=" * 70)
    print("TEAM SECURITY ISOLATION & DATA INTEGRITY TEST SUITE")
    print("=" * 70)

    passed = 0
    failed = 0

    with app.app_context():
        client = app.test_client()

        # Seed official team members
        TeamMember.seed_official_members()

        # ---------------------------------------------------------------------
        # TEST 1: NEW USER REGISTRATION DOES NOT CREATE A TEAM MEMBER
        # ---------------------------------------------------------------------
        print("\n--- TEST 1: New User Registration Isolation ---")
        new_email = 'new_shopper_test@example.com'
        reg_user = User.query.filter_by(email=new_email).first()
        if not reg_user:
            reg_user = User(
                username='new_shopper',
                email=new_email,
                first_name='New',
                last_name='Shopper',
                role=UserRole.USER,
                is_active=True
            )
            reg_user.set_password('Password123!')
            db.session.add(reg_user)
            db.session.commit()

        # Verify reg_user is not in team_members
        tm_user = TeamMember.query.filter_by(email=new_email).first()
        t1_ok = reg_user is not None and tm_user is None
        print(f"1. Registered User Isolation from Team: {'PASSED' if t1_ok else 'FAILED'}")
        if t1_ok: passed += 1
        else: failed += 1

        # ---------------------------------------------------------------------
        # TEST 2: CONTACT FORM SUBMISSION DOES NOT CREATE A TEAM MEMBER
        # ---------------------------------------------------------------------
        print("\n--- TEST 2: Contact Form Submitter Isolation ---")
        contact_res = client.post('/contact', data={
            'name': 'Rahul Applicant',
            'email': 'rahul_applicant@example.com',
            'subject': 'Request to join project team',
            'message': 'Hello, please add me as a team member on your website.'
        }, follow_redirects=True)

        # Message must be in contact_messages
        msg_record = ContactMessage.query.filter_by(email='rahul_applicant@example.com').first()
        # Message must NOT be in team_members
        tm_rahul = TeamMember.query.filter_by(email='rahul_applicant@example.com').first()

        res_contact_page = client.get('/contact')
        html_contact_page = res_contact_page.data.decode('utf-8')

        t2_ok = msg_record is not None and tm_rahul is None and 'Rahul Applicant' not in html_contact_page
        print(f"2. Contact Form Submitter Isolation from Team: {'PASSED' if t2_ok else 'FAILED'}")
        if t2_ok: passed += 1
        else: failed += 1

        # ---------------------------------------------------------------------
        # TEST 3: UNAUTHORIZED TEAM CREATION API ENDPOINTS DO NOT EXIST
        # ---------------------------------------------------------------------
        print("\n--- TEST 3: Reject Unauthorized Team Creation API Requests ---")
        api1 = client.post('/team/add', data={'name': 'Hacker'})
        api2 = client.post('/api/team/add', data={'name': 'Hacker'})
        t3_ok = api1.status_code == 404 and api2.status_code == 404
        print(f"3. Non-Existent Team API Endpoints Rejected (404): {'PASSED' if t3_ok else 'FAILED'}")
        if t3_ok: passed += 1
        else: failed += 1

        # ---------------------------------------------------------------------
        # TEST 4 & 5: NORMAL & ADMIN USER INTERFACE TEAM MANAGEMENT RESTRICTIONS
        # ---------------------------------------------------------------------
        print("\n--- TEST 4 & 5: UI Team Management Restriction ---")
        # Normal user login
        with client:
            with app.test_request_context():
                from flask_login import login_user
                login_user(reg_user)
            html_norm = client.get('/contact').data.decode('utf-8')
            t4_ok = 'Add Team Member' not in html_norm and 'Edit Team Member' not in html_norm and 'Delete Team Member' not in html_norm
            print(f"4. Normal User UI Has Zero Team Management Buttons: {'PASSED' if t4_ok else 'FAILED'}")

        # Admin user login
        admin_user = User.query.filter_by(email='vinuthahemanth7620@gmail.com').first()
        with client:
            with app.test_request_context():
                from flask_login import login_user
                login_user(admin_user)
            html_adm_dash = client.get('/admin/').data.decode('utf-8')
            t5_ok = 'Add Team Member' not in html_adm_dash and 'Create Team Member' not in html_adm_dash
            print(f"5. Admin Dashboard Has Zero Arbitrary Team Member Buttons: {'PASSED' if t5_ok else 'FAILED'}")

        if t4_ok and t5_ok: passed += 1
        else: failed += 1

        # ---------------------------------------------------------------------
        # TEST 6: CONTACT US PAGE DISPLAYS EXCLUSIVELY THE 2 OFFICIAL MEMBERS
        # ---------------------------------------------------------------------
        print("\n--- TEST 6: Contact Us Display Integrity ---")
        res_c = client.get('/contact')
        html_c = res_c.data.decode('utf-8')

        v_present = 'VINUTHA' in html_c and 'AI & Python Backend Developer' in html_c
        t_present = 'THANUSHREE P.H' in html_c and 'Frontend & UI/UX Developer' in html_c
        others_absent = 'Rahul Applicant' not in html_c and 'New Shopper' not in html_c

        t6_ok = v_present and t_present and others_absent
        print(f"6. Contact Us Page Displays Exclusively VINUTHA and THANUSHREE P.H: {'PASSED' if t6_ok else 'FAILED'}")
        if t6_ok: passed += 1
        else: failed += 1

        # ---------------------------------------------------------------------
        # TEST 7: README.md CONTAINS EXCLUSIVELY THE 2 OFFICIAL MEMBERS
        # ---------------------------------------------------------------------
        print("\n--- TEST 7: README.md Integrity ---")
        readme_path = os.path.join(os.path.abspath('.'), 'README.md')
        with open(readme_path, 'r', encoding='utf-8') as f:
            readme_text = f.read()

        rv_present = 'VINUTHA' in readme_text and 'vinuthahemanth7620@gmail.com' in readme_text
        rt_present = 'THANUSHREE P.H' in readme_text and 'thanushreeph14@gmail.com' in readme_text
        rothers_absent = 'Rahul' not in readme_text and 'Shopper' not in readme_text and 'Project Lead' not in readme_text

        t7_ok = rv_present and rt_present and rothers_absent
        print(f"7. README.md Contains Exclusively VINUTHA and THANUSHREE P.H: {'PASSED' if t7_ok else 'FAILED'}")
        if t7_ok: passed += 1
        else: failed += 1

        # ---------------------------------------------------------------------
        # SUMMARY
        # ---------------------------------------------------------------------
        print("\n" + "=" * 70)
        print(f"TEAM SECURITY ISOLATION SUMMARY: {passed} PASSED / {failed} FAILED")
        print("=" * 70)

        return failed == 0


if __name__ == '__main__':
    test_team_security_isolation()
