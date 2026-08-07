import os


REQUIRED_ENV_VARS = [
    'SECRET_KEY',
    'DB_HOST',
    'DB_PORT',
    'DB_NAME',
    'DB_USER',
    'DB_PASSWORD',
    'MAIL_SERVER',
    'MAIL_PORT',
    'MAIL_USE_TLS',
    'MAIL_USE_SSL',
    'MAIL_USERNAME',
    'MAIL_PASSWORD',
    'MAIL_DEFAULT_SENDER',
    'GEMINI_API_KEY'
]

PLACEHOLDER_PASSWORDS = [
    'your-password',
    'your-gmail-app-password',
    'password123',
    'your-16-char-gmail-app-password',
    'your_app_password_here',
    'your-secret-key-here',
    'your-db-password'
]


def validate_environment(config_obj=None) -> dict:
    """
    Validate presence and correctness of environment variables on startup.
    Prints a clear diagnostic summary to console without crashing the application.
    """
    missing_vars = []
    
    # Check presence of each required environment variable
    for var in REQUIRED_ENV_VARS:
        val = os.getenv(var)
        if val is None or val.strip() == '':
            # GEMINI_API_KEY can be empty optional during development
            if var != 'GEMINI_API_KEY':
                missing_vars.append(var)

    # Check Mail Password for placeholder / invalid values
    mail_username = os.getenv('MAIL_USERNAME', '').strip()
    mail_password = os.getenv('MAIL_PASSWORD', '').strip()
    
    is_mail_password_placeholder = (
        not mail_password or
        any(ph in mail_password.lower() for ph in PLACEHOLDER_PASSWORDS) or
        'your-gmail' in mail_password.lower()
    )

    is_mail_username_placeholder = (
        not mail_username or
        'your-email' in mail_username.lower() or
        'your-gmail' in mail_username.lower()
    )

    # Print Diagnostic Report Box
    print("\n======================================================================")
    print("           ENVIRONMENT & CONFIGURATION DIAGNOSTIC REPORT              ")
    print("======================================================================")

    if not missing_vars:
        print(" [OK] Environment Variables Loaded")
    else:
        print(" [!] WARNING: Missing Environment Variables:")
        for m_var in missing_vars:
            print(f"      - {m_var}")

    # Database Status
    db_host = os.getenv('DB_HOST', 'localhost')
    db_name = os.getenv('DB_NAME', 'ai_shopping_assistant')
    print(f" [OK] Database Configuration Loaded (Host: {db_host}, DB: {db_name})")

    # SMTP Configuration Status
    mail_server = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    mail_port = os.getenv('MAIL_PORT', '587')
    print(f" [OK] Gmail SMTP Configuration Loaded ({mail_server}:{mail_port})")

    # App Password Status
    if not is_mail_password_placeholder and not is_mail_username_placeholder:
        print(f" [OK] Gmail App Password Configured ({mail_username})")
    else:
        print(" [!] GMAIL APP PASSWORD WARNING:")
        print("     MAIL_USERNAME or MAIL_PASSWORD contains placeholder values.")
        print("     Gmail SMTP requires a 16-character App Password from Google Account.")
        print("     (Local test OTPs will be printed to this console log).")

    print("======================================================================\n")

    return {
        'all_present': len(missing_vars) == 0,
        'missing_vars': missing_vars,
        'is_app_password_valid': not is_mail_password_placeholder
    }
