from flask import Blueprint

product_bp = Blueprint('product', __name__)


@product_bp.route('/')
def list_products():
    """Product Listing Placeholder Route"""
    return "Product Module Coming Soon"


@product_bp.route('/<int:product_id>')
def product_details(product_id):
    """Product Details Placeholder Route"""
    return "Product Module Coming Soon"
