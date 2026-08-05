from flask import Blueprint

cart_bp = Blueprint('cart', __name__)


@cart_bp.route('/')
def view_cart():
    """Shopping Cart Placeholder Route"""
    return "Shopping Cart Module Coming Soon"
