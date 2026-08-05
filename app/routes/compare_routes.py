from flask import Blueprint, render_template

compare_bp = Blueprint('compare', __name__)


@compare_bp.route('/')
def compare_products():
    """Product Comparison Route"""
    return render_template('main/index.html')
