from datetime import datetime
from sqlalchemy.orm import validates
from app import db


class Product(db.Model):
    """
    Product Model representing items available in the catalog.
    Table: products
    """
    __tablename__ = 'products'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Unique Identifiers & SEO Slugs
    sku = db.Column(db.String(50), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)

    # Core Attributes & Indexed Fields
    name = db.Column(db.String(255), nullable=False, index=True)
    brand = db.Column(db.String(100), nullable=False, index=True)

    # Foreign Key -> Category (Indexed)
    category_id = db.Column(
        db.Integer,
        db.ForeignKey('categories.id', ondelete='RESTRICT'),
        nullable=False,
        index=True
    )

    # Monetary and Rating Metrics (Numeric for currency precision)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    rating = db.Column(db.Numeric(3, 2), default=0.00, nullable=False)

    # Detailed Content & Specifications (Raw Data)
    description = db.Column(db.Text, nullable=True)
    specifications = db.Column(db.JSON, nullable=True)
    image_url = db.Column(db.String(500), nullable=True)

    # Inventory & Status Control
    stock_quantity = db.Column(db.Integer, default=0, nullable=False)
    is_available = db.Column(db.Boolean, default=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Timestamps (Indexed created_at)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Composite Index for Brand + Category queries
    __table_args__ = (
        db.Index('idx_product_brand_category', 'brand', 'category_id'),
    )

    # Relationships
    # One-to-Many: Product -> Cart Items
    cart_items = db.relationship('Cart', backref='product', lazy=True, cascade='all, delete-orphan')

    # One-to-Many: Product -> Wishlist Items
    wishlist_items = db.relationship('Wishlist', backref='product', lazy=True, cascade='all, delete-orphan')

    # One-to-Many: Product -> Order Items
    order_items = db.relationship('OrderItem', backref='product', lazy=True)

    # One-to-Many: Product -> Recommendations
    recommendations = db.relationship('Recommendation', backref='product', lazy=True, cascade='all, delete-orphan')

    # Validations
    @validates('price')
    def validate_price(self, key, value):
        """Validate price is non-negative."""
        if value is not None and float(value) < 0:
            raise ValueError("Product price cannot be negative.")
        return value

    @validates('rating')
    def validate_rating(self, key, value):
        """Validate rating is between 0.0 and 5.0."""
        if value is not None and not (0.0 <= float(value) <= 5.0):
            raise ValueError("Product rating must be between 0.0 and 5.0.")
        return value

    @validates('stock_quantity')
    def validate_stock_quantity(self, key, value):
        """Validate stock quantity is non-negative."""
        if value is not None and int(value) < 0:
            raise ValueError("Product stock quantity cannot be negative.")
        return value

    @property
    def display_short_summary(self):
        """Clean 1-2 sentence product summary."""
        from app.services.product_processor import ProductInformationProcessor
        return ProductInformationProcessor.generate_short_summary(self)

    @property
    def display_key_features(self):
        """Extracted list of 3-4 high-priority key feature bullet points."""
        from app.services.product_processor import ProductInformationProcessor
        return ProductInformationProcessor.extract_important_features(self, limit=3)

    @property
    def display_important_specifications(self):
        """Clean dictionary of useful product specifications for user display."""
        from app.services.product_processor import ProductInformationProcessor
        return ProductInformationProcessor.extract_important_specifications(self)

    @property
    def short_description(self):
        return self.display_short_summary

    @property
    def important_features(self):
        return self.display_key_features

    @property
    def important_specifications(self):
        return self.display_important_specifications

    @property
    def primary_image_url(self):
        """Unified primary image URL property using centralized normalizer."""
        from app.presenters.product_presenter import ProductPresenter
        return ProductPresenter.clean_image_url(self.image_url)

    @property
    def normalized_price_inr(self):
        """Unified price normalizer property for Product model."""
        if self.price is None:
            return 0.0
        raw_p = float(self.price)
        cat_id = self.category_id or 0
        if cat_id <= 4 or raw_p >= 3000.0:
            return raw_p
        return raw_p * 83.0

    def to_dict(self):
        """Convert model instance into dictionary format for API serialization."""
        norm_p = self.normalized_price_inr
        return {
            'id': self.id,
            'sku': self.sku,
            'slug': self.slug,
            'name': self.name,
            'brand': self.brand,
            'category_id': self.category_id,
            'price': norm_p,
            'price_raw_db': float(self.price) if self.price is not None else 0.0,
            'price_formatted': f"₹{norm_p:,.2f}",
            'rating': float(self.rating) if self.rating is not None else 0.0,
            'description': self.description,
            'specifications': self.specifications,
            'short_description': self.display_short_summary,
            'important_features': self.display_key_features,
            'important_specifications': self.display_important_specifications,
            'image_url': self.primary_image_url,
            'stock_quantity': self.stock_quantity,
            'is_available': self.is_available,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<Product {self.name}>'
