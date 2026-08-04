import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config

# Initialize Extensions
db = SQLAlchemy()


def create_app(config_name=None):
    """Application Factory Function"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize Extensions with App
    db.init_app(app)

    # Register Error Handlers
    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)

    # Register Blueprints
    from app.routes.main_routes import main_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.product_routes import product_bp
    from app.routes.ai_routes import ai_bp
    from app.routes.compare_routes import compare_bp
    from app.routes.cart_routes import cart_bp
    from app.routes.profile_routes import profile_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(product_bp, url_prefix='/products')
    app.register_blueprint(ai_bp, url_prefix='/ai')
    app.register_blueprint(compare_bp, url_prefix='/compare')
    app.register_blueprint(cart_bp, url_prefix='/cart')
    app.register_blueprint(profile_bp, url_prefix='/profile')

    return app
