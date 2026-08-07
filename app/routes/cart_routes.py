from flask import Blueprint, render_template
from flask_login import login_required, current_user

cart_bp = Blueprint('cart', __name__)


@cart_bp.route('/')
@login_required
def view_cart():
    """Protected Cart View Route"""
    return render_template('main/index.html')
