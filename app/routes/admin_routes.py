import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.utils.decorators import admin_required
from app.services.admin_service import AdminService
from app.services.product_service import ProductService
from app.presenters.admin_presenter import AdminPresenter
from app.presenters.product_presenter import ProductPresenter

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/')
@admin_required
def dashboard():
    """
    GET /admin/
    Protected Admin Dashboard Route.
    Displays metrics, quick actions, and recent products table.
    """
    view_data = AdminPresenter.prepare_dashboard_view()
    return render_template('admin/dashboard.html', view=view_data)


@admin_bp.route('/products')
@admin_required
def list_products():
    """
    GET /admin/products
    Product Management Listing Route with search, category/stock filtering, and pagination.
    """
    view_data = AdminPresenter.prepare_products_list_view(request.args)
    return render_template('admin/products.html', view=view_data)


@admin_bp.route('/products/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    """
    GET & POST /admin/products/add
    Add Product Form & Processing Route.
    """
    categories = ProductService.get_all_categories()

    if request.method == 'POST':
        form_data = request.form.to_dict()
        is_valid, errors, cleaned_data = AdminPresenter.validate_product_data(form_data)

        if not is_valid:
            flash('Please correct the highlighted errors in the form below.', 'danger')
            return render_template('admin/add_product.html', categories=categories, errors=errors, form_data=form_data)

        try:
            new_prod = AdminService.create_product(cleaned_data)
            flash(f"Product '{new_prod.name}' added successfully!", 'success')
            return redirect(url_for('admin.list_products'))
        except Exception as e:
            flash(f"Error saving product to database: {str(e)}", 'danger')
            return render_template('admin/add_product.html', categories=categories, errors={}, form_data=form_data)

    return render_template('admin/add_product.html', categories=categories, errors={}, form_data={})


@admin_bp.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    """
    GET & POST /admin/products/edit/<product_id>
    Edit Product Form & Update Processing Route.
    """
    product = ProductService.get_product_by_id(product_id)
    if not product:
        flash('Requested product was not found.', 'danger')
        return redirect(url_for('admin.list_products'))

    categories = ProductService.get_all_categories()
    product_card = ProductPresenter.format_product_detail(product)

    if request.method == 'POST':
        form_data = request.form.to_dict()
        is_valid, errors, cleaned_data = AdminPresenter.validate_product_data(form_data)

        if not is_valid:
            flash('Please correct the highlighted errors in the form below.', 'danger')
            return render_template('admin/edit_product.html', product=product_card, categories=categories, errors=errors, form_data=form_data)

        try:
            updated = AdminService.update_product(product_id, cleaned_data)
            if updated:
                flash('Product updated successfully.', 'success')
                return redirect(url_for('admin.list_products'))
            else:
                flash('Failed to update product.', 'danger')
        except Exception as e:
            flash(f"Error updating product: {str(e)}", 'danger')

    # Pre-fill specifications formatted
    specs_raw = product.specifications if isinstance(product.specifications, dict) else {}
    specs_str = json.dumps(specs_raw, indent=2) if specs_raw else ''

    prefilled = {
        'id': product.id,
        'name': product.name,
        'brand': product.brand,
        'category_id': product.category_id,
        'price': float(product.price) if product.price is not None else 0.0,
        'rating': float(product.rating) if product.rating is not None else 0.0,
        'stock_quantity': product.stock_quantity,
        'description': product.description or '',
        'image_url': product.image_url or '',
        'is_available': product.is_available,
        'specifications': specs_str,
        'sku': product.sku,
        'slug': product.slug
    }

    return render_template('admin/edit_product.html', product=product_card, categories=categories, errors={}, form_data=prefilled)


@admin_bp.route('/products/view/<int:product_id>')
@admin_required
def view_product(product_id):
    """
    GET /admin/products/view/<product_id>
    Admin Detailed Product View.
    """
    product = ProductService.get_product_by_id(product_id)
    if not product:
        flash('Requested product was not found.', 'danger')
        return redirect(url_for('admin.list_products'))

    product_data = ProductPresenter.format_product_detail(product)
    return render_template('admin/view_product.html', product=product_data)


@admin_bp.route('/products/delete/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    """
    POST /admin/products/delete/<product_id>
    Delete Product Route (Destructive POST action with confirmation).
    """
    success = AdminService.delete_product(product_id)
    if success:
        flash('Product deleted successfully.', 'success')
    else:
        flash('Failed to delete product or product not found.', 'danger')

    return redirect(url_for('admin.list_products'))
