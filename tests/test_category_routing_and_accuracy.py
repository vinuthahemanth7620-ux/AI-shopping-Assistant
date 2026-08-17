import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from app import create_app
from app.services.ai_service import AIService
from app.recommendation.parser import RequirementParser
from app.recommendation.engine import RecommendationEngine


@pytest.fixture
def app_context():
    app = create_app()
    with app.app_context():
        yield app


def test_conversational_intents(app_context):
    queries = ['hi', 'hello', 'hey', 'what can you do', 'help me', 'thank you', 'bye']
    for q in queries:
        res = AIService.generate_ai_response(q)
        assert res['success'] is True
        assert len(res['recommended_products']) == 0
        assert res['intent'] == 'conversation' or 'Hello' in res['ai_response'] or 'Assistant' in res['ai_response'] or 'welcome' in res['ai_response'] or 'Goodbye' in res['ai_response']


def test_toys_and_games_category(app_context):
    queries = ['toys', 'toy', 'show me toys', 'kids toys', 'board games']
    for q in queries:
        res = AIService.generate_ai_response(q)
        assert res['success'] is True
        prods = res['recommended_products']
        assert len(prods) > 0
        for p in prods:
            assert p.category_id in [38, 39], f"Product {p.name} (cat {p.category_id}) is not a Toy/Game"
            # Ensure no Dewalt battery adapter or catnip
            assert 'dewalt' not in p.name.lower()
            assert 'catnip' not in p.name.lower()


def test_pet_supplies_category(app_context):
    res = AIService.generate_ai_response('pet supplies')
    assert res['success'] is True
    prods = res['recommended_products']
    assert len(prods) > 0
    for p in prods:
        assert p.category_id == 32, f"Product {p.name} (cat {p.category_id}) is not in Pet Supplies"


def test_grocery_category(app_context):
    res = AIService.generate_ai_response('grocery items')
    assert res['success'] is True
    prods = res['recommended_products']
    assert len(prods) > 0
    for p in prods:
        assert p.category_id == 25, f"Product {p.name} (cat {p.category_id}) is not in Grocery"


def test_musical_instruments_category(app_context):
    res = AIService.generate_ai_response('musical instruments')
    assert res['success'] is True
    prods = res['recommended_products']
    assert len(prods) > 0
    for p in prods:
        assert p.category_id in [30, 28], f"Product {p.name} (cat {p.category_id}) is not in Musical Instruments"


def test_automotive_category(app_context):
    res = AIService.generate_ai_response('car accessories')
    assert res['success'] is True
    prods = res['recommended_products']
    assert len(prods) > 0
    for p in prods:
        assert p.category_id in [13, 16], f"Product {p.name} (cat {p.category_id}) is not in Automotive"


def test_arts_and_crafts_category(app_context):
    res = AIService.generate_ai_response('arts and crafts')
    assert res['success'] is True
    prods = res['recommended_products']
    assert len(prods) > 0
    for p in prods:
        assert p.category_id in [12, 26], f"Product {p.name} (cat {p.category_id}) is not in Arts, Crafts & Sewing"


def test_sports_outdoors_category(app_context):
    res = AIService.generate_ai_response('sports equipment')
    assert res['success'] is True
    prods = res['recommended_products']
    assert len(prods) > 0
    for p in prods:
        assert p.category_id in [35, 5], f"Product {p.name} (cat {p.category_id}) is not in Sports & Outdoors"


def test_smartphones_and_budget(app_context):
    res = AIService.generate_ai_response('smartphones under 50000')
    assert res['success'] is True
    prods = res['recommended_products']
    assert len(prods) > 0
    for p in prods:
        assert p.category_id == 2 or p.category_id == 17
        assert p.normalized_price_inr <= 50000.0


def test_laptops_and_coding(app_context):
    res = AIService.generate_ai_response('laptops for coding')
    assert res['success'] is True
    prods = res['recommended_products']
    assert len(prods) > 0
    for p in prods:
        assert p.category_id in [1, 20]
