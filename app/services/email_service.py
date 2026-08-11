import ssl
import smtplib
import socket
import traceback
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app, render_template


def check_smtp_configuration(app=None):
    """
    Validate Gmail SMTP Configuration on Application Startup.
    Prints helpful console instructions if App Password is missing or default.
    """
    config_source = app.config if app else (current_app.config if current_app else {})
    
    mail_username = str(config_source.get('MAIL_USERNAME', '')).strip()
    mail_password = str(config_source.get('MAIL_PASSWORD', '')).strip()

    is_placeholder = (
        not mail_username or
        'your-email' in mail_username.lower() or
        'your-gmail' in mail_username.lower() or
        not mail_password or
        'your-gmail' in mail_password.lower()
    )

    if is_placeholder:
        print("\n======================================================================")
        print(" [GMAIL SMTP CONFIGURATION WARNING]")
        print("======================================================================")
        print(" MAIL_USERNAME or MAIL_PASSWORD contains placeholder credentials.")
        print(" To send real emails directly to Gmail inboxes:")
        print("   1. Go to Google Account Settings -> Security (https://myaccount.google.com/security)")
        print("   2. Enable '2-Step Verification'")
        print("   3. Search for 'App passwords' -> Generate App Password (Name: 'AI Shopping Assistant')")
        print("   4. Copy the generated 16-character App Password")
        print("   5. Update your .env file:")
        print("        MAIL_USERNAME=your_actual_gmail@gmail.com")
        print("        MAIL_PASSWORD=16-character-app-password")
        print(" Until configured, generated OTPs will print to this console for local testing.")
        print("======================================================================\n")
        return False
    else:
        print(f"[SMTP OK] Configured with Gmail Username: {mail_username}")
        return True


import logging
from flask_mail import Message
from app import mail

logger = logging.getLogger(__name__)


def send_email_message(to_email: str, subject: str, html_body: str, plain_text_body: str = None) -> tuple[bool, str]:
    """
    Core Email Sending Service using Flask-Mail and Gmail SMTP.
    
    Returns:
        tuple[bool, str]: (Success boolean, Status message)
    """
    if current_app.config.get('TESTING') or current_app.config.get('MAIL_SUPPRESS_SEND'):
        logger.info(f"[TEST SMTP LOG] Suppressed sending email to {to_email} (Subject: '{subject}')")
        return True, "Email suppressed in testing mode."

    mail_server = current_app.config.get('MAIL_SERVER', 'smtp.gmail.com').strip()
    mail_port = int(current_app.config.get('MAIL_PORT', 587))
    mail_username = current_app.config.get('MAIL_USERNAME', '').strip()
    mail_password = current_app.config.get('MAIL_PASSWORD', '').strip()
    
    # Check for placeholder credentials
    is_placeholder = (
        not mail_username or
        'your-email' in mail_username.lower() or
        'your-gmail' in mail_username.lower() or
        not mail_password or
        'your-gmail' in mail_password.lower()
    )

    if is_placeholder:
        dev_msg = "Gmail SMTP credentials not configured in .env. Email delivery skipped."
        print(f"\n[DEV SMTP LOG] Recipient: {to_email} | Subject: {subject}")
        print(f"[DEV NOTICE] {dev_msg}\n")
        logger.warning(f"[SMTP WARNING] {dev_msg} (Recipient: {to_email})")
        return False, dev_msg

    recipient_email = to_email.strip()
    logger.info(f"Sending email to: {recipient_email} | Subject: {subject}")
    print(f"[SMTP DISPATCH] Sending email to: {recipient_email} | Subject: '{subject}'")

    # 1. Primary Attempt: Send via Flask-Mail extension
    try:
        sender_tuple = ("AI Shopping Assistant", mail_username)
        msg = Message(
            subject=subject,
            recipients=[recipient_email],
            body=plain_text_body or '',
            html=html_body,
            sender=sender_tuple
        )
        mail.send(msg)
        print(f"[OK] Email '{subject}' successfully delivered to {to_email} via Flask-Mail")
        logger.info(f"[SMTP SUCCESS] Email '{subject}' delivered to {to_email}")
        return True, "Email delivered successfully!"

    except Exception as fm_err:
        logger.warning(f"[FLASK-MAIL NOTICE] Flask-Mail send failed: {fm_err}. Retrying with direct SMTP...")
        print(f"[SMTP RETRY] Flask-Mail notice: {fm_err}. Attempting direct Gmail SMTP transport...")

    # 2. Fallback Attempt: Direct SMTP Transport with pure envelope sender
    try:
        mail_sender_header = f"AI Shopping Assistant <{mail_username}>"
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = mail_sender_header
        msg['To'] = to_email.strip()

        if plain_text_body:
            msg.attach(MIMEText(plain_text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        context = ssl.create_default_context()
        use_tls = current_app.config.get('MAIL_USE_TLS', True)
        use_ssl = current_app.config.get('MAIL_USE_SSL', False)

        if use_ssl or mail_port == 465:
            with smtplib.SMTP_SSL(mail_server, mail_port, context=context, timeout=15) as server:
                server.login(mail_username, mail_password)
                # Note: from_addr MUST be pure email address string mail_username
                server.sendmail(mail_username, [to_email.strip()], msg.as_string())
        else:
            with smtplib.SMTP(mail_server, mail_port, timeout=15) as server:
                server.ehlo()
                if use_tls:
                    server.starttls(context=context)
                    server.ehlo()
                server.login(mail_username, mail_password)
                # Note: from_addr MUST be pure email address string mail_username
                server.sendmail(mail_username, [to_email.strip()], msg.as_string())

        print(f"[OK] Email '{subject}' successfully delivered to {to_email} via Direct Gmail SMTP")
        logger.info(f"[SMTP SUCCESS] Direct SMTP email '{subject}' delivered to {to_email}")
        return True, "Email delivered successfully!"

    except smtplib.SMTPAuthenticationError as e:
        err_msg = f"Gmail SMTP Authentication Failed for '{mail_username}'. Please check your 16-character App Password in .env."
        print(f"[SMTP AUTH ERROR] {err_msg} Details: {e}")
        logger.error(f"[SMTP AUTH ERROR] {err_msg}", exc_info=True)
        return False, err_msg
    except smtplib.SMTPRecipientsRefused as e:
        err_msg = f"Recipient address '{to_email}' was refused by Gmail SMTP server."
        print(f"[SMTP RECIPIENT REFUSED] {err_msg} Details: {e}")
        logger.error(f"[SMTP RECIPIENT REFUSED] {err_msg}", exc_info=True)
        return False, err_msg
    except (smtplib.SMTPConnectError, socket.timeout, socket.error) as e:
        err_msg = f"Network Connection Error: Could not connect to Gmail SMTP server ({mail_server}:{mail_port}). Details: {str(e)}"
        print(f"[SMTP CONNECT ERROR] {err_msg}")
        logger.error(f"[SMTP CONNECT ERROR] {err_msg}", exc_info=True)
        return False, err_msg
    except smtplib.SMTPException as e:
        err_msg = f"SMTP Protocol Error: {str(e)}"
        print(f"[SMTP PROTOCOL ERROR] {err_msg}")
        logger.error(f"[SMTP PROTOCOL ERROR] {err_msg}", exc_info=True)
        return False, err_msg
    except Exception as e:
        err_msg = f"Unexpected email delivery error: {str(e)}"
        print(f"[SMTP UNEXPECTED ERROR] {err_msg}")
        logger.error(f"[SMTP UNEXPECTED ERROR] {err_msg}", exc_info=True)
        traceback.print_exc()
        return False, err_msg


def send_password_reset_otp(to_email: str, otp_code: str, user_name: str = "User") -> tuple[bool, str]:
    """Send 6-Digit Password Reset OTP Email."""
    print("\n==================================================")
    print("PASSWORD RESET OTP GENERATED")
    print("==================================================")
    print(f"  * Recipient : {to_email}")
    print(f"  * User Name : {user_name}")
    print(f"  * OTP Code  : {otp_code}")
    print("==================================================\n")

    subject = "AI Shopping Assistant - Password Reset OTP"
    current_year = datetime.utcnow().year

    try:
        html_body = render_template('emails/password_reset_otp.html', otp_code=otp_code, user_name=user_name, year=current_year)
    except Exception as e:
        print(f"[WARN] Failed to render password_reset_otp template: {e}")
        html_body = f"<h2>AI Shopping Assistant - Password Reset OTP</h2><p>Hello {user_name},</p><p>Your password reset code is: <strong>{otp_code}</strong></p><p>This code is valid for 10 minutes.</p><p>If you did not request this, ignore this email.</p>"

    plain_text = (
        f"Hello {user_name},\n\n"
        f"Your password reset code is:\n\n"
        f"{otp_code}\n\n"
        f"This code is valid for 10 minutes.\n\n"
        f"If you did not request this, ignore this email."
    )

    return send_email_message(to_email, subject, html_body, plain_text)


def send_password_reset_link(to_email: str, reset_url: str, user_name: str = "User") -> tuple[bool, str]:
    """Send Password Reset Link Email."""
    print("\n==================================================")
    print("PASSWORD RESET LINK GENERATED")
    print("==================================================")
    print(f"  * Recipient : {to_email}")
    print(f"  * User Name : {user_name}")
    print(f"  * Reset URL : {reset_url}")
    print("==================================================\n")

    subject = "AI Shopping Assistant - Password Reset Request"
    current_year = datetime.utcnow().year

    try:
        html_body = render_template('emails/password_reset_link.html', reset_url=reset_url, user_name=user_name, year=current_year)
    except Exception as e:
        print(f"[WARN] Failed to render password_reset_link template: {e}")
        html_body = f"<h2>AI Shopping Assistant Password Reset</h2><p>Hello {user_name}, click here to reset your password: <a href='{reset_url}'>{reset_url}</a>. Valid for 15 minutes.</p>"

    plain_text = f"Hello {user_name},\nClick the link below to reset your password:\n{reset_url}\n\nThis link is valid for 15 minutes."

    return send_email_message(to_email, subject, html_body, plain_text)


def send_login_notification(to_email: str, user_name: str, login_time: str, ip_address: str, browser: str = "Standard Browser", operating_system: str = "Unknown OS") -> tuple[bool, str]:
    """Send Real-Time Login Security Notification Email for every successful login."""
    print("\n==================================================")
    print("LOGIN SECURITY NOTIFICATION TRIGGERED")
    print("==================================================")
    print(f"  * Logged-in User Email : {to_email}")
    print(f"  * Recipient Email      : {to_email}")
    print(f"  * User Name            : {user_name}")
    print(f"  * Timestamp            : {login_time}")
    print(f"  * Client IP            : {ip_address}")
    print(f"  * Browser              : {browser}")
    print(f"  * Operating System     : {operating_system}")
    print("==================================================\n")

    subject = "New Login Detected – AI Shopping Assistant"
    current_year = datetime.utcnow().year

    try:
        html_body = render_template(
            'emails/login_notification.html',
            user_name=user_name,
            user_email=to_email,
            login_time=login_time,
            ip_address=ip_address,
            browser=browser,
            operating_system=operating_system,
            year=current_year
        )
    except Exception as e:
        print(f"[WARN] Failed to render login_notification template: {e}")
        html_body = f"""
        <h2>New Login Detected – AI Shopping Assistant</h2>
        <p>Hello {user_name},</p>
        <p>Your AI Shopping Assistant account has been accessed successfully.</p>
        <p>Login Details:<br>- Date & Time: {login_time}<br>- IP Address: {ip_address}<br>- Browser: {browser}<br>- Operating System: {operating_system}</p>
        <p>If this was you, no action is required.</p>
        <p>If this wasn't you, please change your password immediately.</p>
        <p>Thank you,<br>AI Shopping Assistant Team</p>
        """

    plain_text = (
        f"Hello {user_name},\n\n"
        f"Your AI Shopping Assistant account has been accessed successfully.\n\n"
        f"Login Details:\n"
        f"- Date & Time: {login_time}\n"
        f"- IP Address: {ip_address}\n"
        f"- Browser: {browser}\n"
        f"- Operating System: {operating_system}\n\n"
        f"If this was you, no action is required.\n"
        f"If this wasn't you, please change your password immediately.\n\n"
        f"Thank you,\nAI Shopping Assistant Team"
    )

    return send_email_message(to_email, subject, html_body, plain_text)

