import enum
from datetime import datetime
from sqlalchemy.orm import validates
from app import db


class PlannerStatus(str, enum.Enum):
    """Enumeration for Shopping Plan Statuses."""
    DRAFT = 'draft'
    ACTIVE = 'active'
    COMPLETED = 'completed'


class ShoppingPlanner(db.Model):
    """
    ShoppingPlanner Model for managing user budget plans.
    Table: shopping_planner
    """
    __tablename__ = 'shopping_planner'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign Key -> User (Indexed)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Plan Metadata & Budget Metric (Numeric 10,2 for currency precision)
    plan_name = db.Column(db.String(150), nullable=False)
    budget = db.Column(db.Numeric(10, 2), nullable=False)
    target_date = db.Column(db.Date, nullable=True)

    # Saved Items JSON Payload
    selected_items = db.Column(db.JSON, nullable=True)

    # Plan Status using SQLAlchemy Enum
    status = db.Column(
        db.Enum(PlannerStatus, name='planner_status'),
        default=PlannerStatus.DRAFT,
        nullable=False
    )

    # Timestamps (Indexed created_at)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    @validates('budget')
    def validate_budget(self, key, value):
        """Validate budget is non-negative."""
        if value is not None and float(value) < 0:
            raise ValueError("Shopping plan budget cannot be negative.")
        return value

    def to_dict(self):
        """Convert model instance into dictionary format for API serialization."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'plan_name': self.plan_name,
            'budget': float(self.budget) if self.budget is not None else 0.0,
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'selected_items': self.selected_items,
            'status': self.status.value if isinstance(self.status, PlannerStatus) else self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<ShoppingPlanner {self.plan_name}>'
