import pytest
from app import create_app, db
from app.models.user import User, UserRole
from app.models.product import Product
from app.models.cart import Cart
from app.models.order import Order, OrderItem


@pytest.fixture
def client():
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        # Seed test user
        user = User.query.filter_by(email='buynow_user@test.com').first()
        if not user:
            user = User(
                username='buynow_user',
                email='buynow_user@test.com',
                first_name='Buy',
                last_name='Tester',
                role=UserRole.USER,
                is_active=True
            )
            user.set_password('Password123!')
            db.session.add(user)
            db.session.commit()
        
        # Seed test product
        p = Product.query.filter_by(sku='BUYNOW-TEST-001').first()
        if not p:
            p = Product(
                sku='BUYNOW-TEST-001',
                slug='buynow-test-product',
                name='Buy Now Test Laptop',
                brand='TestBrand',
                category_id=1,
                price=50000.0,
                rating=4.8,
                stock_quantity=10,
                is_available=True,
                is_active=True
            )
            db.session.add(p)
            db.session.commit()

    with app.test_client() as test_client:
        test_client.app = app
        yield test_client


def test_buy_now_unauthenticated_redirect(client):
    """Test 1: Unauthenticated user clicking Buy Now is redirected to login."""
    with client.app.app_context():
        p = Product.query.filter_by(sku='BUYNOW-TEST-001').first()
        res = client.post(f'/orders/buy-now/{p.id}?quantity=2', follow_redirects=False)
        assert res.status_code == 302
        assert '/auth/login' in res.location


def test_buy_now_authenticated_flow(client):
    """Test 2: Authenticated Buy Now initializes checkout and leaves cart untouched."""
    with client.app.app_context():
        user = User.query.filter_by(email='buynow_user@test.com').first()
        p = Product.query.filter_by(sku='BUYNOW-TEST-001').first()

        # Login test user
        client.post('/auth/login', data={'email': 'buynow_user@test.com', 'password': 'Password123!'})

        # Add a dummy item to cart first
        client.post(f'/cart/add/{p.id}', data={'quantity': 1})
        cart_count_before = Cart.query.filter_by(user_id=user.id).count()

        # Execute Buy Now for 2 units
        buy_res = client.post(f'/orders/buy-now/{p.id}?quantity=2', follow_redirects=True)
        assert buy_res.status_code == 200
        assert b'Checkout' in buy_res.data or b'Direct Purchase Summary' in buy_res.data

        # Place Order from Checkout
        place_res = client.post('/orders/checkout', data={
            'full_name': 'Buy Tester',
            'email': 'buynow_user@test.com',
            'phone': '9876543210',
            'shipping_address': '123 Test Street',
            'city': 'Bangalore',
            'postal_code': '560001',
            'payment_method': 'Cash on Delivery'
        }, follow_redirects=True)

        assert place_res.status_code == 200
        assert b'Order Placed Successfully' in place_res.data or b'ORD-' in place_res.data

        # Verify Cart items remained intact!
        cart_count_after = Cart.query.filter_by(user_id=user.id).count()
        assert cart_count_after == cart_count_before

        # Verify Order was created in DB with correct product, quantity=2, and total=100000
        latest_order = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).first()
        assert latest_order is not None
        assert float(latest_order.total_amount) == 100000.0
        assert len(latest_order.items) == 1
        assert latest_order.items[0].quantity == 2
        assert latest_order.items[0].product_id == p.id
