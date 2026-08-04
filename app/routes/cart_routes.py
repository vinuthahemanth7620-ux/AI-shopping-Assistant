from flask import Blueprint, render_template

cart_bp = Blueprint('cart', __name__)


@cart_bp.route('/')
def view_cart():
    """Cart View Route (Foundation Skeleton)"""
    return render_template('main/index.html')


@cart_bp.route('/planner')
def view_planner():
    """Shopping Planner Route (Foundation Skeleton)"""
    return render_template('main/index.html')
