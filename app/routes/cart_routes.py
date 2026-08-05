from flask import Blueprint, render_template

cart_bp = Blueprint('cart', __name__)


@cart_bp.route('/')
def view_cart():
    """Cart View Route"""
    return render_template('main/index.html')
