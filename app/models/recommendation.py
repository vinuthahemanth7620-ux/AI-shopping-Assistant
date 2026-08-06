from datetime import datetime
from sqlalchemy.orm import validates
from app import db


class Recommendation(db.Model):
    """
    Recommendation Model storing personalized product recommendation scores.
    Table: recommendations
    """
    __tablename__ = 'recommendations'

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

    # Recommendation Metric (Numeric 5,2 for precision score e.g., 0.00 to 1.00 / 100.00)
    recommendation_score = db.Column(
        db.Numeric(5, 2),
        default=0.00,
        nullable=False
    )
    reason = db.Column(db.String(255), nullable=True)

    # Timestamp (Indexed created_at)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    @validates('recommendation_score')
    def validate_recommendation_score(self, key, value):
        """Validate recommendation score is within valid range (0.00 to 1.00 / 100.00)."""
        if value is not None and not (0.0 <= float(value) <= 100.0):
            raise ValueError("Recommendation score must be between 0.00 and 100.00.")
        return value

    def to_dict(self):
        """Convert model instance into dictionary format for API serialization."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'recommendation_score': float(self.recommendation_score) if self.recommendation_score is not None else 0.0,
            'reason': self.reason,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Recommendation User={self.user_id} Product={self.product_id}>'
