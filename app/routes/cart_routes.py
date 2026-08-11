from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.cart import Cart
from app.models.product import Product

cart_bp = Blueprint('cart', __name__)


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
        flash("Product not found or unavailable.", "danger")
        return redirect(request.referrer or url_for('product.list_products'))

    try:
        qty = int(request.form.get('quantity', request.args.get('quantity', 1)))
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
        flash(f'"{product.name[:45]}" added to cart successfully!', "success")
    except Exception as e:
        db.session.rollback()
        flash("An error occurred while adding the product to your cart.", "danger")

    return redirect(request.referrer or url_for('cart.view_cart'))


@cart_bp.route('/update/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    """Update item quantity in cart (increase, decrease, or set quantity >= 1)."""
    cart_item = Cart.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    action = request.form.get('action')

    if action == 'increase':
        cart_item.quantity += 1
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
        else:
            flash("Quantity cannot be less than 1. Use remove to delete item.", "warning")
            return redirect(url_for('cart.view_cart'))
    else:
        try:
            new_qty = int(request.form.get('quantity', cart_item.quantity))
            if new_qty >= 1:
                cart_item.quantity = new_qty
            else:
                flash("Quantity must be at least 1.", "warning")
                return redirect(url_for('cart.view_cart'))
        except (ValueError, TypeError):
            pass

    try:
        db.session.commit()
        flash("Cart quantity updated.", "success")
    except Exception:
        db.session.rollback()
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
        flash(f'Removed "{product_name[:45]}" from cart.', "info")
    except Exception:
        db.session.rollback()
        flash("Failed to remove item from cart.", "danger")

    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/clear', methods=['POST'])
@login_required
def clear_cart():
    """Clear all items from current user's cart."""
    try:
        Cart.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        flash("Your cart has been cleared.", "info")
    except Exception:
        db.session.rollback()
        flash("Failed to clear cart.", "danger")

    return redirect(url_for('cart.view_cart'))
