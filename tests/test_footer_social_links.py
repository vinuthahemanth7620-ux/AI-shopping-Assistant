import os
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath('.'))

from app import create_app


def test_footer_social_links():
    app = create_app()
    app.config['TESTING'] = True

    print("=" * 70)
    print("FOOTER & README TEAM SOCIAL LINKS VERIFICATION TEST SUITE")
    print("=" * 70)

    passed = 0
    failed = 0

    with app.app_context():
        client = app.test_client()

        # 1. Fetch homepage (which includes footer.html)
        res_home = client.get('/')
        html_footer = res_home.data.decode('utf-8')

        v_gh = 'https://github.com/vinuthahemanth7620'
        v_li = 'https://www.linkedin.com/in/vinutha467304310'
        t_gh = 'https://github.com/thanushreeph14-del'
        t_li = 'https://www.linkedin.com/in/thanushree-ph'

        print("\n--- TEST GROUP 1: FOOTER SOCIAL LINKS ---")
        t1_ok = v_gh in html_footer and 'VINUTHA' in html_footer
        print(f"1. Vinutha GitHub Link in Footer ({v_gh}): {'PASSED' if t1_ok else 'FAILED'}")
        if t1_ok: passed += 1
        else: failed += 1

        t2_ok = v_li in html_footer
        print(f"2. Vinutha LinkedIn Link in Footer ({v_li}): {'PASSED' if t2_ok else 'FAILED'}")
        if t2_ok: passed += 1
        else: failed += 1

        t3_ok = t_gh in html_footer and 'THANUSHREE P.H' in html_footer
        print(f"3. Thanushree P.H GitHub Link in Footer ({t_gh}): {'PASSED' if t3_ok else 'FAILED'}")
        if t3_ok: passed += 1
        else: failed += 1

        t4_ok = t_li in html_footer
        print(f"4. Thanushree P.H LinkedIn Link in Footer ({t_li}): {'PASSED' if t4_ok else 'FAILED'}")
        if t4_ok: passed += 1
        else: failed += 1

        # 2. Fetch Contact Us Page
        print("\n--- TEST GROUP 2: CONTACT US PAGE SOCIAL LINKS ---")
        res_contact = client.get('/contact')
        html_contact = res_contact.data.decode('utf-8')

        tc1_ok = v_gh in html_contact and v_li in html_contact and t_gh in html_contact and t_li in html_contact
        print(f"5. All 4 Team Social Links in Contact Us Page: {'PASSED' if tc1_ok else 'FAILED'}")
        if tc1_ok: passed += 1
        else: failed += 1

        # 3. Verify README.md
        print("\n--- TEST GROUP 3: README.MD SOCIAL LINKS ---")
        readme_path = os.path.join(os.path.abspath('.'), 'README.md')
        with open(readme_path, 'r', encoding='utf-8') as f:
            readme_text = f.read()

        r1_ok = v_gh in readme_text and v_li in readme_text and t_gh in readme_text and t_li in readme_text
        print(f"6. All 4 Exact Team Social Links in README.md: {'PASSED' if r1_ok else 'FAILED'}")
        if r1_ok: passed += 1
        else: failed += 1

        print("\n" + "=" * 70)
        print(f"FOOTER & README SOCIAL LINKS SUMMARY: {passed} PASSED / {failed} FAILED")
        print("=" * 70)

        return failed == 0


if __name__ == '__main__':
    test_footer_social_links()
