import logging
from flask import jsonify
from flask_login import current_user
from app import db
from app.models.chat_history import ChatHistory
from app.services.ai_service import AIService
from app.presenters.product_presenter import ProductPresenter

logger = logging.getLogger(__name__)

class AIPresenter:
    """
    AI Presenter Layer - Bridges View/Route requests with AIService business logic,
    validates user input, formats product cards via ProductPresenter, and manages ChatHistory persistence.
    Follows MVP Architecture.
    """

    MAX_MESSAGE_LENGTH = 500

    @classmethod
    def validate_input(cls, message_text):
        """
        Validate incoming chat message text.
        Returns (is_valid, cleaned_message_or_error_string).
        """
        if not message_text or not isinstance(message_text, str):
            return False, "Please enter a non-empty shopping question."
        
        cleaned = message_text.strip()
        if len(cleaned) == 0:
            return False, "Please enter a valid shopping question."
        
        if len(cleaned) > cls.MAX_MESSAGE_LENGTH:
            return False, f"Message is too long. Please restrict your question to {cls.MAX_MESSAGE_LENGTH} characters."

        return True, cleaned

    @classmethod
    def process_chat_request(cls, message_text, user_id=None):
        """
        Main Presenter action for handling POST /ai/chat AJAX requests.
        """
        # 1. Validate Input
        is_valid, validation_result = cls.validate_input(message_text)
        if not is_valid:
            return {
                'success': False,
                'user_message': message_text,
                'ai_response': validation_result,
                'recommended_products': [],
                'intent': 'invalid_input'
            }, 400

        user_message = validation_result

        # 2. Retrieve recent chat history for conversation context
        conversation_context = []
        if user_id:
            recent_logs = ChatHistory.query.filter_by(user_id=user_id)\
                .order_by(ChatHistory.created_at.desc())\
                .limit(5).all()
            recent_logs.reverse()
            for log in recent_logs:
                conversation_context.append({
                    'user_message': log.user_message,
                    'ai_response': log.ai_response
                })
        else:
            try:
                from flask import session
                conversation_context = session.get('guest_chat_history', [])[-5:]
            except Exception:
                conversation_context = []

        # 3. Call AI Service
        ai_result = AIService.generate_ai_response(
            user_query=user_message,
            user_id=user_id,
            conversation_history=conversation_context
        )

        ai_response_text = ai_result.get('ai_response', '')
        raw_products = ai_result.get('recommended_products', [])
        intent = ai_result.get('intent', 'general')

        # 4. Format recommended products into card view objects using ProductPresenter
        formatted_products = []
        for p in raw_products:
            try:
                card = ProductPresenter.format_product_card(p)
                if card:
                    formatted_products.append(card)
            except Exception as e:
                logger.error(f"Error formatting product card for product ID {getattr(p, 'id', 'unknown')}: {str(e)}")

        # 5. Persist Chat History (DB for authenticated users, Session for guest users)
        if user_id:
            try:
                chat_entry = ChatHistory(
                    user_id=user_id,
                    user_message=user_message,
                    ai_response=ai_response_text,
                    intent=intent
                )
                db.session.add(chat_entry)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                logger.error(f"Failed to save ChatHistory for user {user_id}: {str(e)}")
        else:
            try:
                from flask import session
                guest_history = session.get('guest_chat_history', [])
                guest_history.append({
                    'user_message': user_message,
                    'ai_response': ai_response_text
                })
                session['guest_chat_history'] = guest_history[-10:]
            except Exception as e:
                logger.error(f"Failed to save guest session history: {str(e)}")

        return {
            'success': True,
            'user_message': user_message,
            'ai_response': ai_response_text,
            'recommended_products': formatted_products,
            'intent': intent
        }, 200

    @classmethod
    def get_user_chat_history(cls, user_id, limit=20):
        """
        Fetch formatted chat history for authenticated user.
        """
        if not user_id:
            return []

        try:
            logs = ChatHistory.query.filter_by(user_id=user_id)\
                .order_by(ChatHistory.created_at.asc())\
                .limit(limit).all()
            return [log.to_dict() for log in logs]
        except Exception as e:
            logger.error(f"Error fetching chat history for user {user_id}: {str(e)}")
            return []

    @classmethod
    def clear_user_chat_history(cls, user_id=None):
        """
        Delete ChatHistory database records for logged-in user or clear guest session logs.
        """
        if user_id:
            try:
                ChatHistory.query.filter_by(user_id=user_id).delete()
                db.session.commit()
                return True, "Chat history deleted from database."
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error clearing chat history for user {user_id}: {str(e)}")
                return False, f"Error clearing database history: {str(e)}"
        else:
            try:
                from flask import session
                session['guest_chat_history'] = []
                return True, "Guest session chat history cleared."
            except Exception as e:
                logger.error(f"Error clearing guest session chat history: {str(e)}")
                return False, f"Error clearing guest history: {str(e)}"
