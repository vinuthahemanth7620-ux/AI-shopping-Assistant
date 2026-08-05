from datetime import datetime
from app import db


class ShoppingPlanner(db.Model):
    __tablename__ = 'shopping_planner'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    plan_name = db.Column(db.String(150), nullable=False)
    budget = db.Column(db.Numeric(10, 2), nullable=False)
    target_date = db.Column(db.Date, nullable=True)
    selected_items = db.Column(db.JSON, nullable=True)  # List of product IDs and metadata
    status = db.Column(db.Enum('draft', 'active', 'completed', name='plan_status'), default='draft', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<ShoppingPlanner User:{self.user_id} Plan:{self.plan_name}>'
