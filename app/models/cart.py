from datetime import datetime
from sqlalchemy.orm import validates
from app import db


class Cart(db.Model):
    """
    Cart Model representing active cart items for users.
    Table: cart
    """
    __tablename__ = 'cart'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign Keys (Indexed)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    product_id = db.Column(
        db.Integer,
        db.ForeignKey('products.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Item Quantity & Timestamp (Indexed)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Table Constraints: Unique user + product pair
    __table_args__ = (
        db.UniqueConstraint('user_id', 'product_id', name='uq_user_product_cart'),
    )

    @validates('quantity')
    def validate_quantity(self, key, value):
        """Validate item quantity is at least 1."""
        if value is not None and int(value) < 1:
            raise ValueError("Cart item quantity must be at least 1.")
        return value

    def to_dict(self):
        """Convert model instance into dictionary format for API serialization."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'added_at': self.added_at.isoformat() if self.added_at else None
        }

    def __repr__(self):
        return f'<Cart User={self.user_id} Product={self.product_id}>'
