from flask import Blueprint, render_template
from flask_login import login_required, current_user

ai_bp = Blueprint('ai', __name__)


@ai_bp.route('/assistant')
@login_required
def ai_assistant():
    """Protected AI Assistant Chat Interface Route"""
    return render_template('main/index.html')


@ai_bp.route('/recommendations')
@login_required
def recommendations():
    """Protected AI Product Recommendations Route"""
    return render_template('main/index.html')


@ai_bp.route('/chat-history')
@login_required
def chat_history():
    """Protected User Chat History Log Route"""
    return render_template('main/index.html')
