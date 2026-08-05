from flask import Blueprint, render_template

ai_bp = Blueprint('ai', __name__)


@ai_bp.route('/assistant')
def ai_assistant():
    """AI Assistant Chat Interface Route"""
    return render_template('main/index.html')


@ai_bp.route('/recommendations')
def recommendations():
    """AI Product Recommendations Route"""
    return render_template('main/index.html')
