import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from config import config

# Initialize Extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()

# Configure LoginManager Settings
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'


def create_app(config_name=None):
    """Application Factory Function"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config['default']))

    # Print non-sensitive database connection parameters for verification
    if app.config.get('DEBUG') or os.environ.get('FLASK_ENV') == 'development':
        print("\n==================================================")
        print("DATABASE CONFIGURATION VERIFICATION")
        print("==================================================")
        print(f"  * DB Host : {app.config.get('DB_HOST')}")
        print(f"  * DB Port : {app.config.get('DB_PORT')}")
        print(f"  * DB User : {app.config.get('DB_USER')}")
        print(f"  * DB Name : {app.config.get('DB_NAME')}")
        print("==================================================\n")
        
        # Run Startup Environment & SMTP Configuration Diagnostic Validation
        from app.utils.env_validator import validate_environment
        validate_environment(app.config)



    # Initialize Extensions with App
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)

    # Import ORM Models before migrations and loader setup
    from app import models
    from app.models.user import User

    # User Loader Callback for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register Error Handlers
    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)

    # Register Blueprints
    from app.routes.main_routes import main_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.product_routes import product_bp
    from app.routes.ai_routes import ai_bp
    from app.routes.compare_routes import compare_bp
    from app.routes.planner_routes import planner_bp
    from app.routes.cart_routes import cart_bp
    from app.routes.profile_routes import profile_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(product_bp, url_prefix='/products')
    app.register_blueprint(ai_bp, url_prefix='/ai')
    app.register_blueprint(compare_bp, url_prefix='/compare')
    app.register_blueprint(planner_bp, url_prefix='/planner')
    app.register_blueprint(cart_bp, url_prefix='/cart')
    app.register_blueprint(profile_bp, url_prefix='/profile')

    return app
