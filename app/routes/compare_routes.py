from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.models.product import Product
from app.presenters.product_presenter import ProductPresenter

compare_bp = Blueprint('compare', __name__)


@compare_bp.route('/')
def compare_products():
    """
    Product Comparison Route.
    Supports querying product IDs via query params (p1, p2, p3 or products=1,2,3).
    Renders side-by-side product comparison view.
    """
    p_ids_raw = []
    
    # Check comma-separated products or individual p1, p2, p3 params
    if request.args.get('products'):
        p_ids_raw = request.args.get('products', '').split(',')
    else:
        for key in ['p1', 'p2', 'p3']:
            val = request.args.get(key)
            if val:
                p_ids_raw.append(val)

    p_ids = []
    for pid in p_ids_raw:
        try:
            p_ids.append(int(pid.strip()))
        except (ValueError, TypeError):
            pass

    compared_products = []
    if p_ids:
        db_products = Product.query.filter(Product.id.in_(p_ids), Product.is_active == True).all()
        # Maintain requested order
        prod_map = {p.id: p for p in db_products}
        for pid in p_ids:
            if pid in prod_map:
                compared_products.append(ProductPresenter.format_product_detail(prod_map[pid]))

    # If fewer than 2 products selected, fetch top 2 sample products for comparison preview
    sample_products = []
    if len(compared_products) < 2:
        top_samples = Product.query.filter_by(is_active=True).order_by(Product.rating.desc()).limit(4).all()
        sample_products = [ProductPresenter.format_product_card(p) for p in top_samples]

    return render_template(
        'compare.html',
        compared_products=compared_products,
        sample_products=sample_products
    )
