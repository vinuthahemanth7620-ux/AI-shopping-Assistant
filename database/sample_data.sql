-- ====================================================================
-- AI SHOPPING ASSISTANT - SAMPLE DATASEED SCRIPT
-- ====================================================================

USE `ai_shopping_assistant`;

-- Insert Initial Categories
INSERT INTO `categories` (`id`, `name`, `slug`, `description`) VALUES
(1, 'Laptops', 'laptops', 'High performance laptops, ultrabooks, and gaming laptops.'),
(2, 'Mobiles', 'mobiles', 'Smartphones with cutting edge cameras, processors, and display tech.'),
(3, 'Headphones', 'headphones', 'Over-ear, in-ear, and wireless noise-canceling headphones.'),
(4, 'Smart Watches', 'smart-watches', 'Fitness trackers and feature-packed smartwatches.');

-- Insert Sample Products

-- 1. LAPTOPS
INSERT INTO `products` (`name`, `brand`, `category_id`, `price`, `rating`, `description`, `specifications`, `image_url`, `stock_quantity`) VALUES
(
    'MacBook Air M3 15-inch',
    'Apple',
    1,
    129990.00,
    4.8,
    'Supercharged by M3, the 15-inch MacBook Air is insanely thin and fast with up to 18 hours of battery life.',
    '{"Processor": "Apple M3 8-Core", "RAM": "16GB Unified", "Storage": "512GB SSD", "Display": "15.3-inch Liquid Retina", "Weight": "1.51 kg", "OS": "macOS Sonoma"}',
    'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=500',
    25
),
(
    'Dell XPS 13 9340',
    'Dell',
    1,
    144990.00,
    4.6,
    'Iconic minimalist design crafted with CNC aluminum, featuring Intel Core Ultra 7 and OLED Touch Display.',
    '{"Processor": "Intel Core Ultra 7 155H", "RAM": "32GB LPDDR5x", "Storage": "1TB PCIe NVMe SSD", "Display": "13.4-inch 3K OLED Touch", "Weight": "1.19 kg", "OS": "Windows 11 Home"}',
    'https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=500',
    18
),
(
    'Asus ROG Zephyrus G16',
    'Asus',
    1,
    189990.00,
    4.7,
    'Ultra-thin gaming power machine with NVIDIA GeForce RTX 4070 and ROG Nebula OLED 240Hz screen.',
    '{"Processor": "Intel Core Ultra 9 185H", "RAM": "32GB LPDDR5X", "Storage": "1TB Gen4 SSD", "Graphics": "NVIDIA RTX 4070 8GB", "Display": "16-inch 2.5K OLED 240Hz", "Weight": "1.85 kg"}',
    'https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500',
    12
);

-- 2. MOBILES
INSERT INTO `products` (`name`, `brand`, `category_id`, `price`, `rating`, `description`, `specifications`, `image_url`, `stock_quantity`) VALUES
(
    'iPhone 15 Pro Max',
    'Apple',
    2,
    159900.00,
    4.9,
    'Forged in titanium with A17 Pro chip, customizable Action button, and versatile 5x Telephoto camera.',
    '{"Processor": "A17 Pro Chip", "RAM": "8GB", "Storage": "256GB", "Camera": "48MP Main + 12MP Ultra Wide + 12MP 5x Telephoto", "Display": "6.7-inch Super Retina XDR 120Hz", "Battery": "4422 mAh"}',
    'https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=500',
    30
),
(
    'Samsung Galaxy S24 Ultra',
    'Samsung',
    2,
    129999.00,
    4.8,
    'Welcome to the era of mobile AI with Galaxy AI, built-in S Pen, Titanium frame, and 200MP camera.',
    '{"Processor": "Snapdragon 8 Gen 3 for Galaxy", "RAM": "12GB", "Storage": "512GB", "Camera": "200MP + 50MP + 12MP + 10MP", "Display": "6.8-inch Quad HD+ Dynamic AMOLED 2X", "Battery": "5000 mAh"}',
    'https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=500',
    40
),
(
    'Google Pixel 8 Pro',
    'Google',
    2,
    106999.00,
    4.5,
    'The most powerful, personal Pixel yet with Google Tensor G3, advanced AI camera editing, and temperature sensor.',
    '{"Processor": "Google Tensor G3", "RAM": "12GB", "Storage": "128GB", "Camera": "50MP Main + 48MP UltraWide + 48MP Telephoto", "Display": "6.7-inch Super Actua Display 120Hz", "Battery": "5050 mAh"}',
    'https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=500',
    22
);

-- 3. HEADPHONES
INSERT INTO `products` (`name`, `brand`, `category_id`, `price`, `rating`, `description`, `specifications`, `image_url`, `stock_quantity`) VALUES
(
    'Sony WH-1000XM5',
    'Sony',
    3,
    29990.00,
    4.8,
    'Industry-leading noise canceling with two processors and 8 microphones for unparalleled calls and music audio.',
    '{"Type": "Over-Ear Wireless", "Noise Cancellation": "HD Noise Canceling Processor QN1", "Battery Life": "30 Hours", "Driver Unit": "30mm", "Bluetooth": "Version 5.2", "Weight": "250g"}',
    'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500',
    50
),
(
    'Bose QuietComfort Ultra',
    'Bose',
    3,
    35900.00,
    4.7,
    'World-class noise cancellation, spatialized audio, and CustomTune technology for personalized sound.',
    '{"Type": "Over-Ear Wireless", "Audio Tech": "Immersive Spatial Audio", "Battery Life": "24 Hours", "Charging": "USB-C Fast Charge", "Bluetooth": "Version 5.3", "Weight": "252g"}',
    'https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=500',
    35
),
(
    'Apple AirPods Max',
    'Apple',
    3,
    59900.00,
    4.6,
    'Apple-designed dynamic driver provides high-fidelity audio with Computational audio and Active Noise Cancellation.',
    '{"Type": "Over-Ear Wireless", "Chip": "Apple H1 Chip (each ear cup)", "Battery Life": "20 Hours", "Spatial Audio": "Dynamic Head Tracking", "Weight": "384.8g"}',
    'https://images.unsplash.com/photo-1583394838336-acd977736f90?w=500',
    15
);

-- 4. SMART WATCHES
INSERT INTO `products` (`name`, `brand`, `category_id`, `price`, `rating`, `description`, `specifications`, `image_url`, `stock_quantity`) VALUES
(
    'Apple Watch Ultra 2',
    'Apple',
    4,
    89900.00,
    4.9,
    'The ultimate sports and adventure watch with S9 SiP, Double Tap gesture, and 3000 nits display brightness.',
    '{"Case Size": "49mm Titanium", "Display": "Always-On Retina 3000 nits", "Water Resistance": "100m", "Battery Life": "Up to 36 Hours", "Sensors": "ECG, Blood Oxygen, Depth Gauge, Temp"}',
    'https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=500',
    20
),
(
    'Samsung Galaxy Watch 6 Classic',
    'Samsung',
    4,
    36999.00,
    4.6,
    'Iconic rotating bezel returns with 20% larger screen, BioActive Sensor, and advanced sleep coaching.',
    '{"Case Size": "47mm Stainless Steel", "Display": "1.5-inch Super AMOLED Sapphire Crystal", "Battery": "425 mAh", "Sensors": "Heart Rate, BIA Sensor, ECG, Sleep Tracking"}',
    'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500',
    28
);
