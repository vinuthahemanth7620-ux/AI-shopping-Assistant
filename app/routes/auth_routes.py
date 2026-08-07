import secrets
import traceback
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user

from app import db
from app.models.user import User, UserRole
from app.models.login_history import LoginHistory
from app.presenters.auth_presenter import AuthPresenter
from app.services.email_service import (
    send_password_reset_otp,
    send_password_reset_link,
    send_login_notification
)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    User Registration Route
    - Validates mandatory fields & email format.
    - Prevents duplicate email registration.
    - Securely hashes password using Werkzeug.
    - Redirects directly to Login page upon success.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # 1. Mandatory Fields Validation
        if not full_name or not email or not password or not confirm_password:
            flash('All fields are required. Please fill out the complete form.', 'danger')
            return render_template('auth/register.html', full_name=full_name, email=email)

        # 2. Email Format Validation
        if '@' not in email or '.' not in email:
            flash('Please enter a valid email address.', 'danger')
            return render_template('auth/register.html', full_name=full_name, email=email)

        # 3. Password Match Validation
        if password != confirm_password:
            flash('Password and Confirm Password do not match. Please re-enter.', 'danger')
            return render_template('auth/register.html', full_name=full_name, email=email)

        # 4. Password Length Validation
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/register.html', full_name=full_name, email=email)

        # 5. Email Uniqueness Validation
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('An account with this email address already exists. Please log in.', 'warning')
            return render_template('auth/register.html', full_name=full_name, email=email)

        # Parse Name
        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        # Generate Unique Username
        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1

        # Create Active User Instance
        new_user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=UserRole.USER,
            is_active=True,
            email_verified=True
        )
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please sign in with your credentials.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            print(f"[REGISTER ERROR] Exception during user creation: {e}")
            traceback.print_exc()
            flash('An error occurred during registration. Please try again.', 'danger')
            return render_template('auth/register.html', full_name=full_name, email=email)

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    User Login Route
    - Direct authentication with email & password.
    - Calls Flask-Login login_user().
    - Immediately redirects to Dashboard/Home.
    - Dispatches non-blocking login notification email post-authentication.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', 'false').lower() in ['true', '1', 'on']

        if not email or not password:
            flash('Please enter both email address and password.', 'danger')
            return render_template('auth/login.html', email=email)

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash('Invalid email address or password. Please check your credentials.', 'danger')
            return render_template('auth/login.html', email=email)

        if not user.is_active:
            flash('Your account has been deactivated. Please contact support.', 'warning')
            return render_template('auth/login.html', email=email)

        # 1. Immediate Authentication via Flask-Login
        session.permanent = True
        login_user(user, remember=remember)
        current_app.logger.info(f"[LOGIN ROUTE] login_user() executed successfully for user: {user.email}")

        # 2. Extract Client Metadata & Store Audit Record
        ip_header = request.headers.get('X-Forwarded-For', request.remote_addr or '127.0.0.1')
        client_ip = ip_header.split(',')[0].strip() if ip_header else '127.0.0.1'
        user_agent_str = request.headers.get('User-Agent', 'Unknown Device')
        ua_info = AuthPresenter.parse_user_agent(user_agent_str)

        try:
            history = LoginHistory(
                user_id=user.id,
                login_time=datetime.utcnow(),
                ip_address=client_ip,
                browser=ua_info['browser'],
                operating_system=ua_info['operating_system'],
                device_name=ua_info['device_name']
            )
            db.session.add(history)
            db.session.commit()
        except Exception as audit_err:
            db.session.rollback()
            current_app.logger.warning(f"[LOGIN AUDIT WARNING] Could not save LoginHistory: {audit_err}")

        # 3. Send Notification Email After Successful Login
        sender_email = current_app.config.get('MAIL_DEFAULT_SENDER') or current_app.config.get('MAIL_USERNAME')
        current_app.logger.info(f"Logged in user: {user.username or user.first_name}")
        current_app.logger.info(f"Recipient: {user.email}")
        current_app.logger.info(f"Sender: {sender_email}")

        try:
            user_display_name = user.first_name if user.first_name else user.username
            timestamp_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
            success, mail_msg = send_login_notification(
                to_email=user.email,
                user_name=user_display_name,
                login_time=timestamp_str,
                ip_address=client_ip,
                browser=ua_info['browser'],
                operating_system=ua_info['operating_system']
            )
            if success:
                current_app.logger.info("Email successfully sent.")
            else:
                current_app.logger.warning(f"[LOGIN NOTIFICATION WARNING] Status: {mail_msg}")
        except Exception as notify_err:
            current_app.logger.exception(notify_err)

        user_display_name = user.first_name if user.first_name else user.username
        flash(f'Welcome back, {user_display_name}!', 'success')

        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)

        return redirect(url_for('main.dashboard'))

    return render_template('auth/login.html')


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """
    Forgot Password Request Route
    - Generates secure 6-digit numeric OTP (10-min expiry).
    - Dispatches password reset OTP email.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()

        if not email:
            flash('Please enter your registered email address.', 'danger')
            return render_template('auth/forgot_password.html')

        user = User.query.filter_by(email=email).first()

        if not user:
            flash('No account found with that email address.', 'danger')
            return render_template('auth/forgot_password.html', email=email)

        # Generate Secure 6-Digit Numeric OTP (10-minute expiry)
        otp_code = str(secrets.randbelow(900000) + 100000)
        otp_expiry = datetime.utcnow() + timedelta(minutes=10)

        user.forgot_password_otp = otp_code
        user.forgot_password_otp_expiry = otp_expiry
        db.session.commit()

        session['reset_otp_email'] = email
        user_name = user.first_name or user.username

        current_app.logger.info(f"[FORGOT PASSWORD] Generated OTP code: {otp_code} for user: {user.email}")

        success, mail_msg = send_password_reset_otp(email, otp_code, user_name=user_name)

        if success:
            flash('Password reset OTP sent to your email address! Please enter it below.', 'info')
        else:
            flash('Password reset OTP generated! Check server logs if testing locally.', 'warning')

        return redirect(url_for('auth.verify_reset_otp'))

    return render_template('auth/forgot_password.html')


@auth_bp.route('/verify-reset-otp', methods=['GET', 'POST'])
def verify_reset_otp():
    """
    Verify Password Reset OTP Route
    - Validates 6-digit OTP code and expiry (10-min window).
    - Redirects to Reset Password page on success.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    prefill_email = session.get('reset_otp_email', '')

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        otp = request.form.get('otp', '').strip()

        current_app.logger.info(f"[VERIFY OTP] Verification attempt for email: {email}, OTP: {otp}")

        if not email or not otp:
            flash('Please enter both your registered email and the 6-digit OTP code.', 'danger')
            return render_template('auth/verify_reset_otp.html', email=email)

        user = User.query.filter_by(email=email).first()

        if not user or not user.forgot_password_otp:
            current_app.logger.warning(f"[VERIFY OTP] Failed: No pending OTP for user {email}")
            flash('Invalid OTP code or email address. Please request a new code.', 'danger')
            return render_template('auth/verify_reset_otp.html', email=email)

        if user.forgot_password_otp != otp:
            current_app.logger.warning(f"[VERIFY OTP] Failed: Wrong OTP entered for user {email}")
            flash('Invalid OTP code. Please check your email and try again.', 'danger')
            return render_template('auth/verify_reset_otp.html', email=email)

        if not user.forgot_password_otp_expiry or datetime.utcnow() > user.forgot_password_otp_expiry:
            current_app.logger.warning(f"[VERIFY OTP] Failed: Expired OTP for user {email}")
            flash('OTP code has expired (valid for 10 minutes). Please request a new OTP.', 'danger')
            return render_template('auth/verify_reset_otp.html', email=email)

        session['reset_verified_email'] = user.email
        current_app.logger.info(f"[VERIFY OTP] Success: OTP verified for user {user.email}")
        flash('OTP code verified successfully! Please enter your new password.', 'success')
        return redirect(url_for('auth.reset_password'))

    return render_template('auth/verify_reset_otp.html', email=prefill_email)


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """
    Reset Password Route
    - Updates user password hash after OTP verification.
    - Clears OTP and expiry from database.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    email = session.get('reset_verified_email')

    if not email:
        flash('Session expired or unauthorized access. Please request a password reset.', 'warning')
        return redirect(url_for('auth.forgot_password'))

    user = User.query.filter_by(email=email).first()

    if not user:
        flash('User account not found.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not password or not confirm_password:
            flash('All password fields are required.', 'danger')
            return render_template('auth/reset_password.html')

        if password != confirm_password:
            flash('New Password and Confirm Password do not match.', 'danger')
            return render_template('auth/reset_password.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/reset_password.html')

        user.set_password(password)
        user.forgot_password_otp = None
        user.forgot_password_otp_expiry = None
        db.session.commit()

        session.pop('reset_verified_email', None)
        session.pop('reset_otp_email', None)

        current_app.logger.info(f"[RESET PASSWORD] Password updated successfully for user {user.email}")
        flash('Password updated successfully. Please log in with your new password.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """
    User Logout Route
    - Calls Flask-Login logout_user().
    - Clears session state.
    """
    logout_user()
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))
