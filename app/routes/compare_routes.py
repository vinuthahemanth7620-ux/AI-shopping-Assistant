from flask import Blueprint

compare_bp = Blueprint('compare', __name__)


@compare_bp.route('/')
def compare_products():
    """Product Comparison Placeholder Route"""
    return "Product Comparison Module Coming Soon"
