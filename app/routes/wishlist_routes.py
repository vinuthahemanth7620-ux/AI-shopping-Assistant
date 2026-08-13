from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.wishlist import Wishlist
from app.models.product import Product
from app.presenters.product_presenter import ProductPresenter

wishlist_bp = Blueprint('wishlist', __name__)


def wants_json(req):
    """Helper to detect if incoming HTTP request expects a JSON response."""
    return (
        req.is_json or
        req.headers.get('X-Requested-With') == 'XMLHttpRequest' or
        req.headers.get('Accept') == 'application/json' or
        req.args.get('json') == '1'
    )


@wishlist_bp.route('/')
@login_required
def view_wishlist():
    """Protected Wishlist View Route displaying user's wishlisted products."""
    items = Wishlist.query.filter_by(user_id=current_user.id).order_by(Wishlist.created_at.desc()).all()
    
    formatted_products = []
    for item in items:
        if item.product and item.product.is_active:
            p_dict = ProductPresenter.format_product_card(item.product)
            p_dict['wishlist_id'] = item.id
            formatted_products.append(p_dict)

    return render_template(
        'wishlist.html',
        products=formatted_products,
        wishlist_count=len(formatted_products)
    )


@wishlist_bp.route('/toggle/<int:product_id>', methods=['POST'])
@login_required
def toggle_wishlist(product_id):
    """Toggle a product's wishlist status for current user (Add if absent, Remove if present)."""
    product = Product.query.filter_by(id=product_id, is_active=True).first()
    if not product:
        msg = "Product not found or unavailable."
        if wants_json(request):
            return jsonify({'success': False, 'message': msg}), 404
        flash(msg, 'danger')
        return redirect(request.referrer or url_for('product.list_products'))

    item = Wishlist.query.filter_by(user_id=current_user.id, product_id=product.id).first()
    is_wishlisted = False

    try:
        if item:
            db.session.delete(item)
            db.session.commit()
            is_wishlisted = False
            msg = f'Removed "{product.name[:40]}" from your wishlist.'
        else:
            new_item = Wishlist(user_id=current_user.id, product_id=product.id)
            db.session.add(new_item)
            db.session.commit()
            is_wishlisted = True
            msg = f'Added "{product.name[:40]}" to your wishlist!'

        count = Wishlist.query.filter_by(user_id=current_user.id).count()

        if wants_json(request):
            return jsonify({
                'success': True,
                'is_wishlisted': is_wishlisted,
                'wishlist_count': count,
                'product_id': product.id,
                'message': msg
            }), 200

        flash(msg, 'success' if is_wishlisted else 'info')
    except Exception as e:
        db.session.rollback()
        err_msg = "An error occurred while updating your wishlist."
        if wants_json(request):
            return jsonify({'success': False, 'message': err_msg}), 500
        flash(err_msg, 'danger')

    return redirect(request.referrer or url_for('wishlist.view_wishlist'))


@wishlist_bp.route('/remove/<int:product_id>', methods=['POST'])
@login_required
def remove_from_wishlist(product_id):
    """Remove a product from user's wishlist."""
    item = Wishlist.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if item:
        try:
            db.session.delete(item)
            db.session.commit()
            count = Wishlist.query.filter_by(user_id=current_user.id).count()
            msg = "Item removed from wishlist."
            if wants_json(request):
                return jsonify({'success': True, 'message': msg, 'wishlist_count': count}), 200
            flash(msg, 'info')
        except Exception:
            db.session.rollback()
            if wants_json(request):
                return jsonify({'success': False, 'message': "Failed to remove item."}), 500
            flash("Failed to remove item from wishlist.", 'danger')

    return redirect(url_for('wishlist.view_wishlist'))


@wishlist_bp.route('/status', methods=['GET'])
@login_required
def wishlist_status():
    """Return JSON list of product IDs currently in logged-in user's wishlist."""
    items = Wishlist.query.filter_by(user_id=current_user.id).all()
    wishlisted_ids = [item.product_id for item in items]
    return jsonify({
        'success': True,
        'wishlist_ids': wishlisted_ids,
        'wishlist_count': len(wishlisted_ids)
    }), 200
