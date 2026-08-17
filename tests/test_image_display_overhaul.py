import pytest
from app import create_app, db
from app.models.product import Product
from app.presenters.product_presenter import ProductPresenter
from app.presenters.admin_presenter import AdminPresenter

@pytest.fixture
def app():
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_image_normalizer_unit_cases():
    """Verify all 9 image normalization requirement cases."""
    svg_fallback = "/static/images/placeholder_product.svg"

    # Case 1: Direct HTTP(S) URL
    assert ProductPresenter.clean_image_url("https://m.media-amazon.com/images/I/81bw.jpg") == "https://m.media-amazon.com/images/I/81bw.jpg"

    # Case 2: Markdown URL format
    assert ProductPresenter.clean_image_url("![alt](https://example.com/item.png)") == "https://example.com/item.png"
    assert ProductPresenter.clean_image_url("[link](https://example.com/photo.jpg)") == "https://example.com/photo.jpg"

    # Case 3: List of URLs (JSON or Python list)
    assert ProductPresenter.clean_image_url('["https://example.com/first.jpg", "https://example.com/second.jpg"]') == "https://example.com/first.jpg"
    assert ProductPresenter.clean_image_url(["https://example.com/a.jpg", "https://example.com/b.jpg"]) == "https://example.com/a.jpg"

    # Case 4: Empty string or whitespace
    assert ProductPresenter.clean_image_url("") == svg_fallback
    assert ProductPresenter.clean_image_url("   ") == svg_fallback

    # Case 5: None, null, NaN strings
    assert ProductPresenter.clean_image_url(None) == svg_fallback
    assert ProductPresenter.clean_image_url("None") == svg_fallback
    assert ProductPresenter.clean_image_url("NaN") == svg_fallback
    assert ProductPresenter.clean_image_url("null") == svg_fallback
    assert ProductPresenter.clean_image_url("[]") == svg_fallback
    assert ProductPresenter.clean_image_url("{}") == svg_fallback

    # Case 6: Relative static path
    assert ProductPresenter.clean_image_url("static/images/products/macbook.jpg") == "/static/images/products/macbook.jpg"
    assert ProductPresenter.clean_image_url("/static/images/products/macbook.jpg") == "/static/images/products/macbook.jpg"

    # Case 7: Invalid string / XSS script
    assert ProductPresenter.clean_image_url("javascript:alert(1)") == svg_fallback
    assert ProductPresenter.clean_image_url("invalid_random_string") == svg_fallback


def test_product_model_primary_image_url(app):
    """Verify Product model primary_image_url property and to_dict integration."""
    with app.app_context():
        p1 = Product(name="Test Product 1", price=100.0, image_url="![alt](https://img.com/pic.jpg)")
        assert p1.primary_image_url == "https://img.com/pic.jpg"
        
        dict1 = p1.to_dict()
        assert dict1['image_url'] == "https://img.com/pic.jpg"

        p2 = Product(name="Test Product 2", price=200.0, image_url="NaN")
        assert p2.primary_image_url == "/static/images/placeholder_product.svg"
        assert p2.to_dict()['image_url'] == "/static/images/placeholder_product.svg"


def test_admin_presenter_image_validation(app):
    """Verify AdminPresenter validation and normalization for image URLs."""
    with app.app_context():
        form_valid = {
            'name': 'New Admin Keyboard',
            'brand': 'Logitech',
            'category_id': '1',
            'price': '1500',
            'rating': '4.5',
            'stock_quantity': '10',
            'description': 'Mechanical keyboard',
            'image_url': '  https://images.com/keyboard.jpg  '
        }
        is_valid, errors, cleaned = AdminPresenter.validate_product_data(form_valid)
        assert is_valid is True
        assert cleaned['image_url'] == 'https://images.com/keyboard.jpg'

        form_invalid_img = {
            'name': 'New Admin Mouse',
            'brand': 'Logitech',
            'category_id': '1',
            'price': '800',
            'rating': '4.0',
            'stock_quantity': '5',
            'description': 'Wireless mouse',
            'image_url': 'NaN'
        }
        is_valid2, errors2, cleaned2 = AdminPresenter.validate_product_data(form_invalid_img)
        assert is_valid2 is True
        assert cleaned2['image_url'] == '/static/images/placeholder_product.svg'
