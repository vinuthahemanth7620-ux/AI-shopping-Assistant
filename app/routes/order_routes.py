import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.cart import Cart
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product

order_bp = Blueprint('order', __name__)


@order_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """Protected Checkout Route displaying order summary & handling order placement."""
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()

    if not cart_items:
        flash("Your cart is empty. Please add products before checking out.", "warning")
        return redirect(url_for('product.list_products'))

    cart_total = sum(item.subtotal for item in cart_items)
    cart_total_formatted = f"₹{cart_total:,.2f}"

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('shipping_address', '').strip()
        city = request.form.get('city', '').strip()
        postal_code = request.form.get('postal_code', '').strip()
        payment_method = request.form.get('payment_method', 'Cash on Delivery').strip()

        if not full_name or not email or not phone or not address or not city or not postal_code:
            flash("All shipping details are required. Please complete the form.", "danger")
            return render_template(
                'checkout.html',
                cart_items=cart_items,
                cart_total=cart_total,
                cart_total_formatted=cart_total_formatted
            )

        # Generate unique order number
        order_num = f"ORD-{uuid.uuid4().hex[:8].upper()}"

        try:
            new_order = Order(
                order_number=order_num,
                user_id=current_user.id,
                total_amount=cart_total,
                status=OrderStatus.PENDING,
                full_name=full_name,
                email=email,
                phone=phone,
                shipping_address=address,
                city=city,
                postal_code=postal_code,
                payment_method=payment_method
            )
            db.session.add(new_order)
            db.session.flush()  # Obtain new_order.id

            # Create OrderItems & update product stock if needed
            for cart_item in cart_items:
                order_item = OrderItem(
                    order_id=new_order.id,
                    product_id=cart_item.product_id,
                    product_name=cart_item.product.name if cart_item.product else "Product",
                    unit_price=cart_item.unit_price,
                    quantity=cart_item.quantity
                )
                db.session.add(order_item)

            # Clear user's active cart
            Cart.query.filter_by(user_id=current_user.id).delete()
            db.session.commit()

            flash(f"Order #{new_order.order_number} placed successfully! Thank you for shopping with us.", "success")
            return redirect(url_for('order.order_details', order_id=new_order.id))

        except Exception as e:
            db.session.rollback()
            flash("An error occurred while processing your order. Please try again.", "danger")

    return render_template(
        'checkout.html',
        cart_items=cart_items,
        cart_total=cart_total,
        cart_total_formatted=cart_total_formatted
    )


@order_bp.route('/')
@order_bp.route('/history')
@login_required
def my_orders():
    """Display logged-in user's order history."""
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=orders)


@order_bp.route('/<int:order_id>')
@login_required
def order_details(order_id):
    """Display details for a specific order owned by current user (or admin)."""
    order = Order.query.get_or_404(order_id)

    # Authorization Check
    is_admin = current_user.role == 'admin' or (hasattr(current_user.role, 'value') and current_user.role.value == 'admin')
    if order.user_id != current_user.id and not is_admin:
        flash("You are not authorized to view this order.", "danger")
        return redirect(url_for('order.my_orders'))

    return render_template('order_details.html', order=order)
