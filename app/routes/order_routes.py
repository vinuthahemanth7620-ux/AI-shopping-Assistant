import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.cart import Cart
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product

order_bp = Blueprint('order', __name__)


@order_bp.route('/buy-now/<int:product_id>', methods=['GET', 'POST'])
def buy_now(product_id):
    """
    Direct single-product 'Buy Now' action.
    Validates product availability and quantity, stores purchase session, and routes directly to checkout.
    If unauthenticated, redirects to login and returns seamlessly.
    """
    from flask import session

    try:
        qty = int(request.values.get('quantity', 1))
        if qty < 1:
            qty = 1
    except (ValueError, TypeError):
        qty = 1

    product = Product.query.get(product_id)
    if not product or not product.is_active or not product.is_available:
        flash("Selected product is currently unavailable for purchase.", "danger")
        return redirect(url_for('product.list_products'))

    if product.stock_quantity is not None and product.stock_quantity < qty:
        flash(f"Only {product.stock_quantity} units available in stock.", "warning")
        qty = max(1, product.stock_quantity)

    # Store single-item Buy Now intent in session
    session['buy_now_item'] = {
        'product_id': product.id,
        'quantity': qty
    }

    if not current_user.is_authenticated:
        flash("Please log in to complete your instant purchase.", "info")
        return redirect(url_for('auth.login', next=url_for('order.checkout', buy_now=1)))

    return redirect(url_for('order.checkout', buy_now=1))


@order_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """
    Protected Checkout Route.
    Supports both 'Buy Now' single-item checkout and standard multi-item 'Cart' checkout.
    """
    from flask import session

    is_buy_now = request.args.get('buy_now') == '1' or bool(session.get('buy_now_item'))
    buy_now_data = session.get('buy_now_item') if is_buy_now else None

    buy_now_product = None
    buy_now_qty = 1
    buy_now_total = 0.0
    buy_now_total_formatted = "₹0.00"

    cart_items = []
    cart_total = 0.0
    cart_total_formatted = "₹0.00"

    if is_buy_now and buy_now_data:
        p_id = buy_now_data.get('product_id')
        buy_now_qty = buy_now_data.get('quantity', 1)
        buy_now_product = Product.query.get(p_id)

        if not buy_now_product or not buy_now_product.is_active or not buy_now_product.is_available:
            session.pop('buy_now_item', None)
            flash("The selected item for Buy Now is no longer available.", "danger")
            return redirect(url_for('product.list_products'))

        unit_price = float(buy_now_product.normalized_price_inr)
        buy_now_total = unit_price * buy_now_qty
        buy_now_total_formatted = f"₹{buy_now_total:,.2f}"
    else:
        is_buy_now = False
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
                is_buy_now=is_buy_now,
                buy_now_product=buy_now_product,
                buy_now_quantity=buy_now_qty,
                buy_now_total=buy_now_total,
                buy_now_total_formatted=buy_now_total_formatted,
                cart_items=cart_items,
                cart_total=cart_total,
                cart_total_formatted=cart_total_formatted
            )

        # Generate unique order number
        order_num = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        order_total = buy_now_total if is_buy_now else cart_total

        try:
            new_order = Order(
                order_number=order_num,
                user_id=current_user.id,
                total_amount=order_total,
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

            if is_buy_now and buy_now_product:
                unit_p = float(buy_now_product.normalized_price_inr)
                order_item = OrderItem(
                    order_id=new_order.id,
                    product_id=buy_now_product.id,
                    product_name=buy_now_product.name,
                    unit_price=unit_p,
                    quantity=buy_now_qty
                )
                db.session.add(order_item)

                if buy_now_product.stock_quantity is not None and buy_now_product.stock_quantity >= buy_now_qty:
                    buy_now_product.stock_quantity -= buy_now_qty

                # Clear Buy Now session without touching active cart
                session.pop('buy_now_item', None)
            else:
                for cart_item in cart_items:
                    order_item = OrderItem(
                        order_id=new_order.id,
                        product_id=cart_item.product_id,
                        product_name=cart_item.product.name if cart_item.product else "Product",
                        unit_price=cart_item.unit_price,
                        quantity=cart_item.quantity
                    )
                    db.session.add(order_item)
                    if cart_item.product and cart_item.product.stock_quantity is not None and cart_item.product.stock_quantity >= cart_item.quantity:
                        cart_item.product.stock_quantity -= cart_item.quantity

                # Clear user's active cart
                Cart.query.filter_by(user_id=current_user.id).delete()

            db.session.commit()

            flash(f"Order #{new_order.order_number} placed successfully!", "success")
            return redirect(url_for('order.order_success', order_id=new_order.id))

        except Exception as e:
            db.session.rollback()
            flash("An error occurred while processing your order. Please try again.", "danger")

    return render_template(
        'checkout.html',
        is_buy_now=is_buy_now,
        buy_now_product=buy_now_product,
        buy_now_quantity=buy_now_qty,
        buy_now_total=buy_now_total,
        buy_now_total_formatted=buy_now_total_formatted,
        cart_items=cart_items,
        cart_total=cart_total,
        cart_total_formatted=cart_total_formatted
    )


@order_bp.route('/success/<int:order_id>')
@login_required
def order_success(order_id):
    """Clean Order Confirmation View after successful placement."""
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash("You are not authorized to view this order.", "danger")
        return redirect(url_for('order.my_orders'))

    return render_template('order_success.html', order=order)


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
