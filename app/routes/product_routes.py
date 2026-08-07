from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.services.product_service import ProductService
from app.presenters.product_presenter import ProductPresenter

product_bp = Blueprint('product', __name__)


@product_bp.route('/')
@login_required
def list_products():
    """
    Product Catalog Listing Route.
    Authenticated users can browse, search, filter, sort, and paginate products.
    """
    # Extract query parameters
    query_params = request.args.to_dict()

    search_query = request.args.get('q', '').strip()
    category_id = request.args.get('category', '').strip()
    brand = request.args.get('brand', '').strip()
    min_price = request.args.get('min_price', '').strip()
    max_price = request.args.get('max_price', '').strip()
    min_rating = request.args.get('min_rating', '').strip()
    sort_by = request.args.get('sort', 'newest').strip()
    page = request.args.get('page', 1, type=int)

    # 1. Fetch categories and brands for filter UI
    categories = ProductService.get_all_categories()
    brands = ProductService.get_all_brands()
    price_bounds = ProductService.get_price_bounds()

    # 2. Fetch filtered products with pagination (12 items per page)
    pagination = ProductService.get_filtered_products(
        search_query=search_query,
        category_id=category_id,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        sort_by=sort_by,
        page=page,
        per_page=12
    )

    # 3. Present data for view
    view_data = ProductPresenter.prepare_catalog_view(
        pagination=pagination,
        categories=categories,
        brands=brands,
        query_params=query_params,
        price_bounds=price_bounds
    )

    return render_template('products.html', view=view_data)


@product_bp.route('/<int:product_id>')
@login_required
def product_details(product_id):
    """
    Product Details Route.
    Displays detailed information, image, pricing, specs, and stock availability for a specific product.
    """
    product = ProductService.get_product_by_id(product_id)

    if not product:
        flash('The requested product was not found or is no longer available.', 'danger')
        return redirect(url_for('product.list_products'))

    product_data = ProductPresenter.format_product_detail(product)

    return render_template('product_details.html', product=product_data)


@product_bp.route('/search')
@login_required
def search_products():
    """
    Dedicated Search Route.
    Processes search queries and renders matching products.
    """
    q = request.args.get('q', '').strip()
    if not q:
        flash('Please enter a search keyword to search products.', 'info')
        return redirect(url_for('product.list_products'))

    return redirect(url_for('product.list_products', q=q))


@product_bp.route('/filter')
@login_required
def filter_products():
    """
    Dedicated Filter Route.
    Redirects filter parameters to list_products.
    """
    params = {k: v for k, v in request.args.items() if v}
    return redirect(url_for('product.list_products', **params))


@product_bp.route('/sort')
@login_required
def sort_products():
    """
    Dedicated Sort Route.
    Redirects sorting parameters to list_products.
    """
    params = {k: v for k, v in request.args.items() if v}
    return redirect(url_for('product.list_products', **params))
