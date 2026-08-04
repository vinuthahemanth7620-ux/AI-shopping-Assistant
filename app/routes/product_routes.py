from flask import Blueprint, render_template

product_bp = Blueprint('product', __name__)


@product_bp.route('/')
def list_products():
    """Product Listing Route (Foundation Skeleton)"""
    return render_template('main/index.html')


@product_bp.route('/<int:product_id>')
def product_details(product_id):
    """Product Details Route (Foundation Skeleton)"""
    return render_template('main/index.html')
