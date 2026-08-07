from datetime import datetime
from app import db


class LoginHistory(db.Model):
    """
    LoginHistory Model - Audit log of user login sessions.
    Table: login_history
    """
    __tablename__ = 'login_history'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    login_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    browser = db.Column(db.String(100), nullable=True)
    operating_system = db.Column(db.String(100), nullable=True)
    device_name = db.Column(db.String(100), nullable=True)

    def to_dict(self):
        """Convert model instance into dictionary format."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'login_time': self.login_time.isoformat() if self.login_time else None,
            'ip_address': self.ip_address,
            'browser': self.browser,
            'operating_system': self.operating_system,
            'device_name': self.device_name
        }

    def __repr__(self):
        return f'<LoginHistory User={self.user_id} Time={self.login_time}>'
