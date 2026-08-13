from datetime import datetime
from app import db


class Wishlist(db.Model):
    """
    Wishlist Model representing user wishlisted products.
    Table: wishlists
    """
    __tablename__ = 'wishlists'

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

    # Timestamp (Indexed)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Table Constraints: Unique user + product pair
    __table_args__ = (
        db.UniqueConstraint('user_id', 'product_id', name='uq_user_product_wishlist'),
    )

    def to_dict(self):
        """Convert model instance into dictionary format for API serialization."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else '',
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Wishlist User={self.user_id} Product={self.product_id}>'
