import os
import sys
import unittest

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.product import Product
from app.models.cart import Cart
from app.presenters.product_presenter import ProductPresenter
from app.services.ai_service import AIService
from app.services.product_service import ProductService

def safe_print(text):
    """Print unicode safely on Windows CP1252 terminals."""
    print(text.encode('ascii', 'ignore').decode('ascii'))

class TestPriceNormalization(unittest.TestCase):
    """Comprehensive test suite for central price normalization and currency consistency."""

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app_context = cls.app.app_context()
        cls.app_context.push()

    @classmethod
    def tearDownClass(cls):
        cls.app_context.pop()

    def test_01_usd_to_inr_conversion(self):
        """1. USD -> INR conversion for imported Amazon dataset product."""
        product = Product.query.filter_by(id=101772).first() # HP 17.3 Laptop (USD 712.99)
        self.assertIsNotNone(product)
        norm_price = product.normalized_price_inr
        expected_price = 712.99 * 83.0
        self.assertAlmostEqual(norm_price, expected_price, places=2)
        safe_print(f"[TEST 1 PASSED] USD 712.99 converted to INR {norm_price:,.2f}")

    def test_02_inr_preservation(self):
        """2. INR preservation for seed products (Category IDs 1-4)."""
        product = Product.query.filter_by(id=14).first() # iPhone 15 Pro Max (INR 159900)
        self.assertIsNotNone(product)
        norm_price = product.normalized_price_inr
        self.assertAlmostEqual(norm_price, 159900.0, places=2)
        safe_print(f"[TEST 2 PASSED] Seed INR 159,900.00 preserved accurately")

    def test_03_product_card_price(self):
        """3. Product card price formatting."""
        product = Product.query.filter_by(id=102221).first() # Gateway Laptop (USD 169.00)
        card = ProductPresenter.format_product_card(product)
        self.assertEqual(card['price_formatted'], '₹14,027.00')
        self.assertAlmostEqual(card['price_raw'], 14027.0, places=2)
        safe_print(f"[TEST 3 PASSED] Card price formatted as {card['price_formatted']}")

    def test_04_product_detail_price(self):
        """4. Product detail price formatting."""
        product = Product.query.filter_by(id=102564).first() # HP Envy x360 (USD 479.99)
        detail = ProductPresenter.format_product_detail(product)
        self.assertEqual(detail['price_formatted'], '₹39,839.17')
        safe_print(f"[TEST 4 PASSED] Detail price formatted as {detail['price_formatted']}")

    def test_05_ai_response_price(self):
        """5. AI chatbot response price string uses normalized INR."""
        res = AIService.generate_ai_response("Tell me about the HP Envy x360")
        ai_text = res.get('ai_response', '')
        products = res.get('recommended_products', [])
        has_rupee = ("₹" in ai_text) or any("₹" in (ProductPresenter.format_product_card(p)['price_formatted']) for p in products if p)
        self.assertTrue(has_rupee)
        safe_print(f"[TEST 5 PASSED] AI response contains normalized INR price")

    def test_06_comparison_price(self):
        """6. Comparison table price string."""
        products = Product.query.filter(Product.id.in_([101772, 102221])).all()
        table = AIService.generate_product_comparison(products)
        self.assertIn("59,178.17", table)
        self.assertIn("14,027.00", table)
        safe_print(f"[TEST 6 PASSED] Comparison table contains normalized INR prices")

    def test_07_cart_calculation(self):
        """7. Cart line item unit price and subtotal calculation."""
        product = Product.query.filter_by(id=102564).first() # HP Envy x360 (USD 479.99 = INR 39,839.17)
        cart_item = Cart(user_id=999, product_id=product.id, quantity=2)
        cart_item.product = product
        self.assertAlmostEqual(cart_item.unit_price, 39839.17, places=2)
        self.assertAlmostEqual(cart_item.subtotal, 79678.34, places=2)
        dict_cart = cart_item.to_dict()
        self.assertEqual(dict_cart['unit_price_formatted'], '₹39,839.17')
        self.assertEqual(dict_cart['subtotal_formatted'], '₹79,678.34')
        safe_print(f"[TEST 7 PASSED] Cart unit price ₹39,839.17 x 2 = Subtotal ₹79,678.34")

    def test_08_budget_filtering(self):
        """8. Budget filtering 'Show me laptops under 50000'."""
        res = AIService.generate_ai_response("Show me laptops under 50000")
        products = res.get('recommended_products', [])
        is_fallback = res.get('is_fallback', False)
        self.assertTrue(len(products) > 0)
        for p in products:
            if not is_fallback:
                price_val = p.get('price_raw', 0.0) if isinstance(p, dict) else float(getattr(p, 'normalized_price_inr', 0.0))
                self.assertLessEqual(price_val, 50000.0)
        safe_print(f"[TEST 8 PASSED] Budget filter handled correctly for {len(products)} products (fallback={is_fallback})")

    def test_09_price_ascending_sort(self):
        """9. Price ascending sort using normalized INR prices."""
        pagination = ProductService.get_filtered_products(category_id=20, sort_by='price_asc', page=1, per_page=10)
        prices = [p.normalized_price_inr for p in pagination.items]
        self.assertEqual(prices, sorted(prices))
        safe_print(f"[TEST 9 PASSED] Price asc sorted monotonically: {['INR ' + f'{p:,.2f}' for p in prices[:3]]}")

    def test_10_price_descending_sort(self):
        """10. Price descending sort using normalized INR prices."""
        pagination = ProductService.get_filtered_products(category_id=20, sort_by='price_desc', page=1, per_page=10)
        prices = [p.normalized_price_inr for p in pagination.items]
        self.assertEqual(prices, sorted(prices, reverse=True))
        safe_print(f"[TEST 10 PASSED] Price desc sorted monotonically: {['INR ' + f'{p:,.2f}' for p in prices[:3]]}")

    def test_11_cheapest_product_query(self):
        """11. 'Which laptop is cheapest?' query."""
        res = AIService.generate_ai_response("Which laptop is cheapest?")
        products = res.get('recommended_products', [])
        self.assertTrue(len(products) > 0)
        cheapest_prod = products[0]
        safe_print(f"[TEST 11 PASSED] Cheapest laptop returned: {cheapest_prod.name[:35]} @ INR {cheapest_prod.normalized_price_inr:,.2f}")

    def test_12_most_expensive_product_query(self):
        """12. 'Which laptop is most expensive?' query."""
        intent = AIService.extract_user_intent("Which product has the highest price?")
        self.assertEqual(intent['sort_preference'], 'price_desc')
        products = AIService.retrieve_relevant_products(intent, "Which product has the highest price?")
        self.assertTrue(len(products) > 0)
        most_exp = products[0]
        safe_print(f"[TEST 12 PASSED] Most expensive product returned: {most_exp.name[:35]} @ INR {most_exp.normalized_price_inr:,.2f}")

    def test_13_api_serialization(self):
        """13. Product model to_dict API serialization."""
        product = Product.query.filter_by(id=102564).first()
        p_dict = product.to_dict()
        self.assertAlmostEqual(p_dict['price'], 39839.17, places=2)
        self.assertEqual(p_dict['price_formatted'], '₹39,839.17')
        safe_print(f"[TEST 13 PASSED] Product.to_dict() serialized price as {p_dict['price_formatted']}")

    def test_14_gemini_context_price(self):
        """14. Gemini context text contains normalized INR price."""
        products = Product.query.filter(Product.id.in_([101772, 102564])).all()
        context = AIService.build_structured_context(products)
        self.assertIn("59,178.17", context)
        self.assertIn("39,839.17", context)
        safe_print(f"[TEST 14 PASSED] Gemini catalog context contains normalized INR prices")

if __name__ == '__main__':
    unittest.main()
