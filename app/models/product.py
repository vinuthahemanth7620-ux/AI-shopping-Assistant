from datetime import datetime
from app import db


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    brand = db.Column(db.String(100), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='RESTRICT'), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    rating = db.Column(db.Numeric(3, 2), default=0.00, nullable=False)
    description = db.Column(db.Text, nullable=True)
    specifications = db.Column(db.JSON, nullable=True)  # JSON specifications dictionary
    image_url = db.Column(db.String(500), nullable=True)
    stock_quantity = db.Column(db.Integer, default=50, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    cart_items = db.relationship('Cart', backref='product', lazy=True, cascade='all, delete-orphan')
    recommendations = db.relationship('Recommendation', backref='product', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Product {self.name}>'
