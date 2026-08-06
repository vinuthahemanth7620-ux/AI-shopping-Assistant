from datetime import datetime
from app import db


class Category(db.Model):
    """
    Category Model for organizing catalog products.
    Table: categories
    """
    __tablename__ = 'categories'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Category Metadata with Indexes
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)

    # Soft Delete / Active Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Timestamp (Indexed for temporal queries)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    # One-to-Many: Category -> Products
    products = db.relationship('Product', backref='category', lazy=True)

    def to_dict(self):
        """Convert model instance into dictionary format for API serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Category {self.name}>'
