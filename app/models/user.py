import enum
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class UserRole(str, enum.Enum):
    """Enumeration for User Roles."""
    USER = 'user'
    ADMIN = 'admin'


class User(UserMixin, db.Model):
    """
    User Model representing system users and administrators.
    Inherits from UserMixin for Flask-Login integration.
    Table: users
    """
    __tablename__ = 'users'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # User Attributes & Credentials with Indexes
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)

    # Role Management using SQLAlchemy Enum
    role = db.Column(
        db.Enum(UserRole, name='user_roles'),
        default=UserRole.USER,
        nullable=False
    )

    # Account Active Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    email_verified = db.Column(db.Boolean, default=True, nullable=False)

    # Password Reset OTP Columns
    forgot_password_otp = db.Column(db.String(10), nullable=True)
    forgot_password_otp_expiry = db.Column(db.DateTime, nullable=True)

    # Legacy Token Columns
    reset_token = db.Column(db.String(100), nullable=True, index=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)


    # Timestamps (Indexed created_at)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    cart_items = db.relationship('Cart', backref='user', lazy=True, cascade='all, delete-orphan')
    chat_histories = db.relationship('ChatHistory', backref='user', lazy=True, cascade='all, delete-orphan')
    recommendations = db.relationship('Recommendation', backref='user', lazy=True, cascade='all, delete-orphan')
    shopping_plans = db.relationship('ShoppingPlanner', backref='user', lazy=True, cascade='all, delete-orphan')
    login_histories = db.relationship('LoginHistory', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        """Securely hash and store the user password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password against stored hash."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Convert model instance into dictionary format for API serialization."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role': self.role.value if isinstance(self.role, UserRole) else self.role,
            'is_active': self.is_active,
            'email_verified': self.email_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<User {self.username}>'
