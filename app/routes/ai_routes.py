from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.presenters.ai_presenter import AIPresenter

ai_bp = Blueprint('ai', __name__)


@ai_bp.route('/')
@ai_bp.route('/assistant')
def ai_assistant():
    """
    Display AI Shopping Assistant page.
    Renders templates/ai/chat.html with preloaded chat history if user is authenticated.
    """
    user_id = current_user.id if (current_user and current_user.is_authenticated) else None
    history = AIPresenter.get_user_chat_history(user_id=user_id, limit=15) if user_id else []
    return render_template('ai/chat.html', initial_history=history)


@ai_bp.route('/chat', methods=['POST'])
@ai_bp.route('/api/chat', methods=['POST'])
@ai_bp.route('/api/assistant', methods=['POST'])
def chat():
    """
    POST /ai/chat, /api/chat, /api/assistant
    Endpoint for sending user questions to AI Shopping Assistant.
    Expects JSON body: {"message": "User query text"}
    """
    try:
        data = request.get_json(silent=True) or {}
        message_text = data.get('message', '').strip()
        
        if not message_text:
            # Fallback to form data if sent via standard form
            message_text = request.form.get('message', '').strip()

        if not message_text:
            return jsonify({
                'success': False,
                'ai_response': 'Please enter a valid question or product request.',
                'recommended_products': []
            }), 400

        user_id = current_user.id if (current_user and current_user.is_authenticated) else None

        result, status_code = AIPresenter.process_chat_request(
            message_text=message_text,
            user_id=user_id
        )

        return jsonify(result), status_code
    except Exception as e:
        return jsonify({
            'success': False,
            'ai_response': 'An error occurred while generating recommendations. Please try again.',
            'recommended_products': [],
            'error': str(e)
        }), 200


@ai_bp.route('/chat-history', methods=['GET'])
def chat_history():
    """
    GET /ai/chat-history
    Retrieve conversation history logs for logged-in user.
    """
    if not current_user or not current_user.is_authenticated:
        return jsonify({'success': False, 'history': [], 'message': 'User not authenticated'}), 401

    history = AIPresenter.get_user_chat_history(user_id=current_user.id, limit=30)
    return jsonify({'success': True, 'history': history}), 200


@ai_bp.route('/clear-history', methods=['POST'])
def clear_history():
    """
    POST /ai/clear-history
    Clear ChatHistory database records for logged-in user or guest session history.
    """
    user_id = current_user.id if (current_user and current_user.is_authenticated) else None
    success, message = AIPresenter.clear_user_chat_history(user_id=user_id)
    return jsonify({'success': success, 'message': message}), 200 if success else 500


@ai_bp.route('/recommendations')
def recommendations():
    """
    Redirect or view for AI product recommendations.
    """
    return ai_assistant()
