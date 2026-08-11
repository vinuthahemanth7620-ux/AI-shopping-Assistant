from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.cart import Cart
from app.models.product import Product

cart_bp = Blueprint('cart', __name__)


from sqlalchemy import func


def wants_json(req):
    """Helper to detect if incoming HTTP request expects a JSON API response."""
    return (
        req.is_json or
        req.headers.get('X-Requested-With') == 'XMLHttpRequest' or
        req.headers.get('Accept') == 'application/json' or
        req.args.get('json') == '1'
    )


@cart_bp.route('/')
@login_required
def view_cart():
    """Protected Cart View Route displaying all items in current user's cart."""
    cart_items = Cart.query.filter_by(user_id=current_user.id).order_by(Cart.added_at.desc()).all()
    cart_total = sum(item.subtotal for item in cart_items)
    cart_total_formatted = f"₹{cart_total:,.2f}"

    return render_template(
        'cart.html',
        cart_items=cart_items,
        cart_total=cart_total,
        cart_total_formatted=cart_total_formatted
    )


@cart_bp.route('/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    """Add a product to current user's active cart or increment quantity."""
    product = Product.query.filter_by(id=product_id, is_active=True).first()

    if not product:
        msg = "Product not found or unavailable."
        if wants_json(request):
            return jsonify({'success': False, 'message': msg}), 404
        flash(msg, "danger")
        return redirect(request.referrer or url_for('product.list_products'))

    # Parse requested quantity safely
    req_json = request.get_json(silent=True) or {}
    try:
        qty = int(req_json.get('quantity') or request.form.get('quantity') or request.args.get('quantity') or 1)
        if qty < 1:
            qty = 1
    except (ValueError, TypeError):
        qty = 1

    cart_item = Cart.query.filter_by(user_id=current_user.id, product_id=product.id).first()

    if cart_item:
        cart_item.quantity += qty
    else:
        cart_item = Cart(user_id=current_user.id, product_id=product.id, quantity=qty)
        db.session.add(cart_item)

    try:
        db.session.commit()
        success_msg = f'"{product.name[:45]}" added to cart successfully!'
        
        # Calculate updated user total cart quantity
        total_count = db.session.query(func.sum(Cart.quantity)).filter(Cart.user_id == current_user.id).scalar() or 0

        if wants_json(request):
            return jsonify({
                'success': True,
                'message': success_msg,
                'cart_count': int(total_count),
                'product_id': product.id,
                'quantity': cart_item.quantity
            }), 200

        flash(success_msg, "success")
    except Exception as e:
        db.session.rollback()
        err_msg = "An error occurred while adding the product to your cart."
        if wants_json(request):
            return jsonify({'success': False, 'message': err_msg}), 500
        flash(err_msg, "danger")

    return redirect(request.referrer or url_for('cart.view_cart'))


@cart_bp.route('/update/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    """Update item quantity in cart (increase, decrease, or set quantity >= 1)."""
    cart_item = Cart.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    req_json = request.get_json(silent=True) or {}
    action = req_json.get('action') or request.form.get('action')

    if action == 'increase':
        cart_item.quantity += 1
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
        else:
            msg = "Quantity cannot be less than 1. Use remove to delete item."
            if wants_json(request):
                return jsonify({'success': False, 'message': msg}), 400
            flash(msg, "warning")
            return redirect(url_for('cart.view_cart'))
    else:
        try:
            raw_q = req_json.get('quantity') or request.form.get('quantity')
            new_qty = int(raw_q if raw_q is not None else cart_item.quantity)
            if new_qty >= 1:
                cart_item.quantity = new_qty
            else:
                msg = "Quantity must be at least 1."
                if wants_json(request):
                    return jsonify({'success': False, 'message': msg}), 400
                flash(msg, "warning")
                return redirect(url_for('cart.view_cart'))
        except (ValueError, TypeError):
            pass

    try:
        db.session.commit()
        
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        cart_total = sum(item.subtotal for item in cart_items)
        total_count = sum(item.quantity for item in cart_items)

        if wants_json(request):
            return jsonify({
                'success': True,
                'message': "Cart quantity updated.",
                'item_id': cart_item.id,
                'quantity': cart_item.quantity,
                'item_subtotal': cart_item.subtotal,
                'item_subtotal_formatted': f"₹{cart_item.subtotal:,.2f}",
                'cart_total': cart_total,
                'cart_total_formatted': f"₹{cart_total:,.2f}",
                'cart_count': total_count
            }), 200

        flash("Cart quantity updated.", "success")
    except Exception:
        db.session.rollback()
        if wants_json(request):
            return jsonify({'success': False, 'message': "Failed to update cart quantity."}), 500
        flash("Failed to update cart quantity.", "danger")

    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    """Remove a specific item from user's cart."""
    cart_item = Cart.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    product_name = cart_item.product.name if cart_item.product else "Product"

    try:
        db.session.delete(cart_item)
        db.session.commit()
        
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        cart_total = sum(item.subtotal for item in cart_items)
        total_count = sum(item.quantity for item in cart_items)

        msg = f'Removed "{product_name[:45]}" from cart.'

        if wants_json(request):
            return jsonify({
                'success': True,
                'message': msg,
                'item_id': item_id,
                'cart_total': cart_total,
                'cart_total_formatted': f"₹{cart_total:,.2f}",
                'cart_count': total_count
            }), 200

        flash(msg, "info")
    except Exception:
        db.session.rollback()
        if wants_json(request):
            return jsonify({'success': False, 'message': "Failed to remove item from cart."}), 500
        flash("Failed to remove item from cart.", "danger")

    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/clear', methods=['POST'])
@login_required
def clear_cart():
    """Clear all items from current user's cart."""
    try:
        Cart.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()

        if wants_json(request):
            return jsonify({'success': True, 'message': "Your cart has been cleared.", 'cart_count': 0}), 200

        flash("Your cart has been cleared.", "info")
    except Exception:
        db.session.rollback()
        if wants_json(request):
            return jsonify({'success': False, 'message': "Failed to clear cart."}), 500
        flash("Failed to clear cart.", "danger")

    return redirect(url_for('cart.view_cart'))

