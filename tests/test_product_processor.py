import pytest
from app import create_app
from app.services.product_processor import ProductInformationProcessor


@pytest.fixture
def app():
    app = create_app('testing')
    app.config['TESTING'] = True
    return app


def test_category_feature_extraction_laptop(app):
    """Test 1: Laptop category feature extraction."""
    mock_product = {
        'name': 'Dell XPS 15 9530 Intel Core i7 16GB RAM 512GB SSD RTX 4050 15.6 inch OLED',
        'category_name': 'Laptops',
        'description': 'High performance laptop with Intel Core i7 13700H, 16GB DDR5 RAM, 512GB NVMe SSD, NVIDIA RTX 4050 graphics and 15.6 inch OLED Touch screen.',
        'specifications': {'Processor': 'Intel Core i7', 'RAM': '16GB', 'Storage': '512GB SSD', 'ASIN': 'B08XYZ1234', 'Package Dimensions': '40 x 30 x 5 cm'}
    }
    extracted = ProductInformationProcessor.extract_important_features(mock_product, limit=3)
    summary = ProductInformationProcessor.generate_short_summary(mock_product)

    assert len(extracted) <= 4
    assert any('Intel Core I7' in f or 'Core i7' in f for f in extracted)
    assert any('16GB' in f for f in extracted)
    assert any('512GB' in f for f in extracted)
    # Ensure ASIN and Package Dimensions are filtered out
    assert not any('ASIN' in f for f in extracted)
    assert not any('Package Dimensions' in f for f in extracted)
    assert len(summary.split()) <= 35


def test_category_feature_extraction_smartphone(app):
    """Test 2: Smartphone category feature extraction."""
    mock_product = {
        'name': 'Samsung Galaxy S24 Ultra 12GB RAM 256GB Storage 200MP Camera 5000mAh Battery 6.8 inch AMOLED',
        'category_name': 'Smartphones',
        'description': 'Flagship mobile phone with 200MP main camera, 5000mAh long-lasting battery, 12GB RAM, and 256GB internal storage.',
        'specifications': {'RAM': '12GB', 'Camera': '200MP', 'Battery': '5000mAh'}
    }
    extracted = ProductInformationProcessor.extract_important_features(mock_product, limit=4)
    assert len(extracted) <= 4
    assert any('12GB' in f for f in extracted)
    assert any('200MP' in f for f in extracted)


def test_category_feature_extraction_headphones(app):
    """Test 3: Headphones category feature extraction."""
    mock_product = {
        'name': 'Sony WH-1000XM5 Wireless Headphones ANC Bluetooth 30 Hours Playtime 40mm Driver',
        'category_name': 'Headphones',
        'description': 'Industry leading noise canceling headphones with Bluetooth 5.2, 30 hours battery playtime, and 40mm drivers.',
        'specifications': {'Noise Cancelling': 'Yes (ANC)', 'Battery': '30 Hours', 'Connectivity': 'Bluetooth 5.2'}
    }
    extracted = ProductInformationProcessor.extract_important_features(mock_product, limit=3)
    assert len(extracted) <= 4
    assert any('Noise Cancel' in f or 'ANC' in f for f in extracted)
    assert any('Bluetooth' in f or 'Wireless' in f for f in extracted)


def test_category_feature_extraction_induction_stove(app):
    """Test 4: Induction stove category feature extraction."""
    mock_product = {
        'name': 'Philips 2100W Induction Cooktop Touch Control 8 Preset Cooking Modes Auto Shut Off',
        'category_name': 'Cooktops & Stoves',
        'description': 'Powerful 2100W induction stove featuring 8 preset cooking modes, touch control panel, and auto shut-off overheat safety.',
        'specifications': {'Power': '2100W', 'Control': 'Touch', 'ASIN': 'B0712345'}
    }
    extracted = ProductInformationProcessor.extract_important_features(mock_product, limit=4)
    assert len(extracted) <= 4
    assert any('2100W' in f for f in extracted)
    assert any('Touch' in f or 'Power' in f or 'Overheat' in f for f in extracted)
    assert not any('ASIN' in f for f in extracted)


def test_category_feature_extraction_washing_machine(app):
    """Test 5: Washing machine category feature extraction."""
    mock_product = {
        'name': 'LG 7kg Front Load Fully Automatic Washing Machine Inverter 1200 RPM 5 Star',
        'category_name': 'Washing Machines',
        'description': 'Fully automatic front load washer with 7kg capacity, 1200 RPM spin speed, and 5 Star energy efficiency rating.',
        'specifications': {'Capacity': '7kg', 'Type': 'Front Load', 'Rating': '5 Star'}
    }
    extracted = ProductInformationProcessor.extract_important_features(mock_product, limit=3)
    assert len(extracted) <= 4
    assert any('7kg' in f or '7KG' in f for f in extracted)
    assert any('Front Load' in f for f in extracted)


def test_category_feature_extraction_shoes(app):
    """Test 6: Shoes category feature extraction."""
    mock_product = {
        'name': 'Nike Air Zoom Pegasus Running Shoes Mesh Breathable Rubber Sole Lace-Up',
        'category_name': 'Shoes & Footwear',
        'description': 'Lightweight running shoes built with breathable mesh upper, rubber sole, and cushioned foam midsole for daily running.',
        'specifications': {'Material': 'Mesh', 'Sole': 'Rubber', 'Use': 'Running'}
    }
    extracted = ProductInformationProcessor.extract_important_features(mock_product, limit=3)
    assert len(extracted) <= 4
    assert any('Mesh' in f or 'Rubber' in f for f in extracted)


def test_category_feature_extraction_office_chair(app):
    """Test 7: Office chair category feature extraction."""
    mock_product = {
        'name': 'Ergonomic Mesh Office Chair Adjustable Lumbar Support 120kg Weight Capacity',
        'category_name': 'Furniture',
        'description': 'High back ergonomic chair with breathable mesh, 2D adjustable lumbar support, pneumatic height adjustment and 120kg capacity.',
        'specifications': {'Material': 'Mesh', 'Weight Capacity': '120kg'}
    }
    extracted = ProductInformationProcessor.extract_important_features(mock_product, limit=3)
    assert len(extracted) <= 4
    assert any('Lumbar' in f or 'Mesh' in f or '120kg' in f for f in extracted)


def test_category_feature_extraction_camera(app):
    """Test 8: Camera category feature extraction."""
    mock_product = {
        'name': 'Canon EOS R6 Mark II Mirrorless Camera 24.2 MP 4K Video 40fps Wireless',
        'category_name': 'Cameras',
        'description': 'Full frame mirrorless camera featuring 24.2 MP CMOS sensor, 4K 60p video recording, and dual pixel CMOS AF II.',
        'specifications': {'Sensor': '24.2 MP', 'Video': '4K UHD'}
    }
    extracted = ProductInformationProcessor.extract_important_features(mock_product, limit=3)
    assert len(extracted) <= 4
    assert any('24.2 MP' in f or 'Sensor' in f for f in extracted)
    assert any('4K' in f for f in extracted)


def test_category_feature_extraction_smartwatch(app):
    """Test 9: Smartwatch category feature extraction."""
    mock_product = {
        'name': 'Apple Watch Series 9 GPS 45mm AMOLED Display Heart Rate SpO2 18 Hours Battery',
        'category_name': 'Smartwatches',
        'description': 'Advanced smartwatch with 45mm always-on Retina AMOLED display, heart rate and SpO2 sensors, and 18 hours battery life.',
        'specifications': {'Display': 'AMOLED', 'Health': 'Heart Rate & SpO2'}
    }
    extracted = ProductInformationProcessor.extract_important_features(mock_product, limit=3)
    assert len(extracted) <= 4
    assert any('AMOLED' in f or 'Display' in f or '45mm' in f for f in extracted)
    assert any('Heart Rate' in f or 'SpO2' in f or 'Health' in f for f in extracted)


def test_category_feature_extraction_kitchen_appliance(app):
    """Test 10: Kitchen appliance category feature extraction."""
    mock_product = {
        'name': 'NutriBullet 900W High Speed Blender Juicer 900 Watts Stainless Steel Blades',
        'category_name': 'Kitchen Appliances',
        'description': 'Compact high-speed nutrient extractor blender with 900W power output, stainless steel blades, and easy-clean cups.',
        'specifications': {'Power': '900W', 'Blades': 'Stainless Steel'}
    }
    extracted = ProductInformationProcessor.extract_important_features(mock_product, limit=3)
    assert len(extracted) <= 4
    assert any('900W' in f for f in extracted)


def test_extract_important_specifications(app):
    """Test 11: Important specifications extraction and metadata filtering."""
    mock_product = {
        'name': 'Cussity Rechargeable LED Flashlight',
        'specifications': {
            'Brand': 'Cussity',
            'Material': 'Aluminum',
            'Power Source': 'Battery Powered',
            'Special Feature': 'Rechargeable',
            'Special Features': 'Rechargeable',
            'ASIN': 'B08XYZ1234',
            'Package Dimensions': '20 x 10 x 5 cm',
            'Date First Available': 'January 1, 2024',
            'Best Sellers Rank': '#1 in Flashlights',
            'Country of Origin': 'China'
        }
    }
    clean_specs = ProductInformationProcessor.extract_important_specifications(mock_product)

    # Useful specs must be present
    assert 'Brand' in clean_specs
    assert clean_specs['Brand'] == 'Cussity'
    assert 'Material' in clean_specs
    assert 'Power Source' in clean_specs
    assert 'Special Feature' in clean_specs
    assert clean_specs['Special Feature'] in ['Rechargeable', 'Yes']

    # Low-value metadata must be filtered out
    assert 'ASIN' not in clean_specs
    assert 'Package Dimensions' not in clean_specs
    assert 'Date First Available' not in clean_specs
    assert 'Best Sellers Rank' not in clean_specs
    assert 'Country of Origin' not in clean_specs
    # Duplicate Special Features key must be deduplicated
    assert 'Special Features' not in clean_specs
