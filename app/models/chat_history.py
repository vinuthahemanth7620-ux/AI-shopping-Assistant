from datetime import datetime
from app import db


class ChatHistory(db.Model):
    """
    ChatHistory Model storing conversation logs with the Gemini AI Assistant.
    Table: chat_history
    """
    __tablename__ = 'chat_history'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign Key -> User (Indexed)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Conversation Content & Intent
    user_message = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text, nullable=False)
    intent = db.Column(db.String(100), nullable=True)

    # Timestamp (Indexed created_at)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    def to_dict(self):
        """Convert model instance into dictionary format for API serialization."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_message': self.user_message,
            'ai_response': self.ai_response,
            'intent': self.intent,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<ChatHistory User={self.user_id}>'
