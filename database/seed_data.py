"""
AI Shopping Assistant - Database Seed Script
Populates database with initial categories, demo users, and sample products with SKUs, Slugs, and local images.
Idempotent design prevents duplicate records on multiple runs.

Usage:
    python database/seed_data.py
"""

import sys
import os
from werkzeug.security import generate_password_hash

# Add parent directory to path so imports work cleanly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.user import User, UserRole
from app.models.category import Category
from app.models.product import Product


# Define Categories
CATEGORIES_DATA = [
    {
        "name": "Laptops",
        "slug": "laptops",
        "description": "High performance laptops, ultrabooks, gaming notebooks, and workstations."
    },
    {
        "name": "Mobiles",
        "slug": "mobiles",
        "description": "Smartphones with cutting edge cameras, high-refresh rate displays, and powerful processors."
    },
    {
        "name": "Headphones",
        "slug": "headphones",
        "description": "Over-ear, in-ear, wireless noise-canceling headphones, and spatial audio earbuds."
    },
    {
        "name": "Smart Watches",
        "slug": "smart-watches",
        "description": "Fitness trackers, outdoor adventure watches, and feature-packed smartwatches."
    }
]


# Sample Products Dataset (~50 products with unique SKUs, Slugs, Local Image Paths, and Ratings)
PRODUCTS_DATA = [
    # ==========================================
    # 1. LAPTOPS (13 Products)
    # ==========================================
    {
        "sku": "LAP001",
        "slug": "macbook-air-m3-15-inch",
        "name": "MacBook Air M3 15-inch",
        "brand": "Apple",
        "category_slug": "laptops",
        "price": 129990.00,
        "rating": 4.8,
        "description": "Supercharged by M3, the 15-inch MacBook Air is insanely thin and fast with up to 18 hours of battery life.",
        "specifications": {
            "Processor": "Apple M3 8-Core CPU",
            "RAM": "16GB Unified Memory",
            "Storage": "512GB SSD",
            "Display": "15.3-inch Liquid Retina",
            "Weight": "1.51 kg"
        },
        "image_url": "static/images/products/macbook_air_m3.jpg",
        "stock_quantity": 25,
        "is_available": True
    },
    {
        "sku": "LAP002",
        "slug": "dell-xps-13-9340",
        "name": "Dell XPS 13 9340",
        "brand": "Dell",
        "category_slug": "laptops",
        "price": 144990.00,
        "rating": 4.6,
        "description": "Iconic minimalist design crafted with CNC aluminum, featuring Intel Core Ultra 7 and 3K OLED Touch Display.",
        "specifications": {
            "Processor": "Intel Core Ultra 7 155H",
            "RAM": "32GB LPDDR5x",
            "Storage": "1TB PCIe NVMe SSD",
            "Display": "13.4-inch 3K OLED Touch",
            "Weight": "1.19 kg"
        },
        "image_url": "static/images/products/dell_xps_13.jpg",
        "stock_quantity": 18,
        "is_available": True
    },
    {
        "sku": "LAP003",
        "slug": "asus-rog-zephyrus-g16",
        "name": "Asus ROG Zephyrus G16",
        "brand": "Asus",
        "category_slug": "laptops",
        "price": 189990.00,
        "rating": 4.7,
        "description": "Ultra-thin gaming power machine with NVIDIA GeForce RTX 4070 and ROG Nebula OLED 240Hz screen.",
        "specifications": {
            "Processor": "Intel Core Ultra 9 185H",
            "RAM": "32GB LPDDR5X",
            "Storage": "1TB Gen4 SSD",
            "Graphics": "NVIDIA RTX 4070 8GB",
            "Display": "16-inch 2.5K OLED 240Hz"
        },
        "image_url": "static/images/products/asus_rog_zephyrus_g16.jpg",
        "stock_quantity": 12,
        "is_available": True
    },
    {
        "sku": "LAP004",
        "slug": "hp-spectre-x360-14",
        "name": "HP Spectre x360 14",
        "brand": "HP",
        "category_slug": "laptops",
        "price": 139990.00,
        "rating": 4.5,
        "description": "2-in-1 convertible touchscreen laptop with 9MP AI camera, haptic touchpad, and IMAX Enhanced OLED display.",
        "specifications": {
            "Processor": "Intel Core Ultra 7 155H",
            "RAM": "16GB LPDDR5x",
            "Storage": "1TB NVMe SSD",
            "Display": "14-inch 2.8K OLED Touch"
        },
        "image_url": "static/images/products/hp_spectre_x360.jpg",
        "stock_quantity": 20,
        "is_available": True
    },
    {
        "sku": "LAP005",
        "slug": "lenovo-thinkpad-x1-carbon-gen-12",
        "name": "Lenovo ThinkPad X1 Carbon Gen 12",
        "brand": "Lenovo",
        "category_slug": "laptops",
        "price": 172990.00,
        "rating": 4.8,
        "description": "The benchmark enterprise ultrabook with carbon-fiber chassis, legendary keyboard, and Intel Evo certification.",
        "specifications": {
            "Processor": "Intel Core Ultra 7 165H",
            "RAM": "32GB LPDDR5x",
            "Storage": "1TB PCIe Gen4 SSD",
            "Display": "14-inch 2.8K OLED"
        },
        "image_url": "static/images/products/lenovo_thinkpad_x1.jpg",
        "stock_quantity": 15,
        "is_available": True
    },
    {
        "sku": "LAP006",
        "slug": "macbook-pro-m3-max-16-inch",
        "name": "MacBook Pro M3 Max 16-inch",
        "brand": "Apple",
        "category_slug": "laptops",
        "price": 349900.00,
        "rating": 4.9,
        "description": "Mind-blowing performance for extreme workflows with 16-core CPU, 40-core GPU, and Liquid Retina XDR screen.",
        "specifications": {
            "Processor": "Apple M3 Max 16-Core",
            "RAM": "48GB Unified Memory",
            "Storage": "1TB SSD",
            "Display": "16.2-inch Liquid Retina XDR"
        },
        "image_url": "static/images/products/macbook_pro_m3_max.jpg",
        "stock_quantity": 8,
        "is_available": True
    },
    {
        "sku": "LAP007",
        "slug": "acer-predator-helios-16",
        "name": "Acer Predator Helios 16",
        "brand": "Acer",
        "category_slug": "laptops",
        "price": 159990.00,
        "rating": 4.6,
        "description": "High-octane gaming beast equipped with Intel Core i9 14th Gen, RTX 4080, and custom Aeroblade 3D cooling.",
        "specifications": {
            "Processor": "Intel Core i9-14900HX",
            "RAM": "32GB DDR5",
            "Storage": "1TB SSD",
            "Graphics": "NVIDIA RTX 4080 12GB"
        },
        "image_url": "static/images/products/acer_predator_helios_16.jpg",
        "stock_quantity": 10,
        "is_available": True
    },
    {
        "sku": "LAP008",
        "slug": "acer-swift-go-14",
        "name": "Acer Swift Go 14",
        "brand": "Acer",
        "category_slug": "laptops",
        "price": 69990.00,
        "rating": 4.4,
        "description": "Sleek and lightweight aluminum budget laptop featuring vivid 90Hz OLED display and long battery backup.",
        "specifications": {
            "Processor": "Intel Core Ultra 5 125H",
            "RAM": "16GB LPDDR5",
            "Storage": "512GB SSD",
            "Display": "14-inch 2.8K OLED"
        },
        "image_url": "static/images/products/acer_swift_go_14.jpg",
        "stock_quantity": 35,
        "is_available": True
    },
    {
        "sku": "LAP009",
        "slug": "microsoft-surface-laptop-6",
        "name": "Microsoft Surface Laptop 6",
        "brand": "Microsoft",
        "category_slug": "laptops",
        "price": 124990.00,
        "rating": 4.5,
        "description": "Sleek touchscreen laptop built for business with Copilot key, PixelSense display, and omnisonic speakers.",
        "specifications": {
            "Processor": "Intel Core Ultra 5 135H",
            "RAM": "16GB LPDDR5x",
            "Storage": "512GB SSD",
            "Display": "13.5-inch PixelSense Touch"
        },
        "image_url": "static/images/products/surface_laptop_6.jpg",
        "stock_quantity": 14,
        "is_available": True
    },
    {
        "sku": "LAP010",
        "slug": "razer-blade-16",
        "name": "Razer Blade 16",
        "brand": "Razer",
        "category_slug": "laptops",
        "price": 299990.00,
        "rating": 4.8,
        "description": "World's first dual-mode Mini-LED display gaming laptop with anodized CNC aluminum unibody chassis.",
        "specifications": {
            "Processor": "Intel Core i9-14900HX",
            "RAM": "32GB DDR5",
            "Storage": "2TB NVMe SSD",
            "Graphics": "NVIDIA RTX 4090 16GB"
        },
        "image_url": "static/images/products/razer_blade_16.jpg",
        "stock_quantity": 6,
        "is_available": True
    },
    {
        "sku": "LAP011",
        "slug": "lenovo-yoga-9i-dual-screen",
        "name": "Lenovo Yoga 9i Dual Screen",
        "brand": "Lenovo",
        "category_slug": "laptops",
        "price": 219990.00,
        "rating": 4.6,
        "description": "Innovative dual 13.3-inch OLED touchscreen laptop with detachable Bluetooth keyboard and Bowers & Wilkins soundbar.",
        "specifications": {
            "Processor": "Intel Core Ultra 7 155H",
            "RAM": "32GB LPDDR5X",
            "Storage": "1TB SSD",
            "Display": "Dual 13.3-inch 2.8K OLED"
        },
        "image_url": "static/images/products/lenovo_yoga_9i.jpg",
        "stock_quantity": 9,
        "is_available": True
    },
    {
        "sku": "LAP012",
        "slug": "asus-zenbook-14-oled",
        "name": "Asus Zenbook 14 OLED",
        "brand": "Asus",
        "category_slug": "laptops",
        "price": 96990.00,
        "rating": 4.5,
        "description": "Ultraportable 1.2kg laptop powered by Intel Core Ultra processor and breathtaking 3K 120Hz ASUS Lumina OLED panel.",
        "specifications": {
            "Processor": "Intel Core Ultra 7 155H",
            "RAM": "16GB LPDDR5X",
            "Storage": "1TB SSD",
            "Display": "14-inch 3K OLED"
        },
        "image_url": "static/images/products/asus_zenbook_14.jpg",
        "stock_quantity": 22,
        "is_available": True
    },
    {
        "sku": "LAP013",
        "slug": "dell-alienware-m18-r2",
        "name": "Dell Alienware m18 R2",
        "brand": "Dell",
        "category_slug": "laptops",
        "price": 314990.00,
        "rating": 4.7,
        "description": "Desktop replacement gaming monster with 18-inch QHD+ 165Hz display and Element 31 thermal interface.",
        "specifications": {
            "Processor": "Intel Core i9-14900HX",
            "RAM": "64GB DDR5",
            "Storage": "2TB SSD",
            "Graphics": "NVIDIA RTX 4090 16GB"
        },
        "image_url": "static/images/products/alienware_m18.jpg",
        "stock_quantity": 5,
        "is_available": True
    },

    # ==========================================
    # 2. MOBILES (13 Products)
    # ==========================================
    {
        "sku": "MOB001",
        "slug": "iphone-15-pro-max",
        "name": "iPhone 15 Pro Max",
        "brand": "Apple",
        "category_slug": "mobiles",
        "price": 159900.00,
        "rating": 4.9,
        "description": "Forged in titanium with A17 Pro chip, customizable Action button, and versatile 5x Telephoto camera.",
        "specifications": {
            "Processor": "Apple A17 Pro Chip",
            "RAM": "8GB",
            "Storage": "256GB",
            "Camera": "48MP + 12MP + 12MP",
            "Battery": "4422 mAh"
        },
        "image_url": "static/images/products/iphone_15_pro_max.jpg",
        "stock_quantity": 30,
        "is_available": True
    },
    {
        "sku": "MOB002",
        "slug": "samsung-galaxy-s24-ultra",
        "name": "Samsung Galaxy S24 Ultra",
        "brand": "Samsung",
        "category_slug": "mobiles",
        "price": 129999.00,
        "rating": 4.8,
        "description": "Welcome to the era of mobile AI with Galaxy AI, built-in S Pen, Titanium frame, and 200MP camera.",
        "specifications": {
            "Processor": "Snapdragon 8 Gen 3",
            "RAM": "12GB",
            "Storage": "512GB",
            "Camera": "200MP Quad Camera",
            "Battery": "5000 mAh"
        },
        "image_url": "static/images/products/galaxy_s24_ultra.jpg",
        "stock_quantity": 40,
        "is_available": True
    },
    {
        "sku": "MOB003",
        "slug": "google-pixel-8-pro",
        "name": "Google Pixel 8 Pro",
        "brand": "Google",
        "category_slug": "mobiles",
        "price": 106999.00,
        "rating": 4.5,
        "description": "The most powerful, personal Pixel yet with Google Tensor G3, advanced AI camera editing, and temperature sensor.",
        "specifications": {
            "Processor": "Google Tensor G3",
            "RAM": "12GB",
            "Storage": "128GB",
            "Camera": "50MP Triple Camera",
            "Battery": "5050 mAh"
        },
        "image_url": "static/images/products/pixel_8_pro.jpg",
        "stock_quantity": 22,
        "is_available": True
    },
    {
        "sku": "MOB004",
        "slug": "iphone-15",
        "name": "iPhone 15",
        "brand": "Apple",
        "category_slug": "mobiles",
        "price": 79900.00,
        "rating": 4.7,
        "description": "Dynamic Island comes to iPhone 15 along with 48MP Main camera, USB-C, and durable color-infused back glass.",
        "specifications": {
            "Processor": "Apple A16 Bionic",
            "RAM": "6GB",
            "Storage": "128GB",
            "Camera": "48MP Dual Camera",
            "Battery": "3349 mAh"
        },
        "image_url": "static/images/products/iphone_15.jpg",
        "stock_quantity": 45,
        "is_available": True
    },
    {
        "sku": "MOB005",
        "slug": "oneplus-12",
        "name": "OnePlus 12",
        "brand": "OnePlus",
        "category_slug": "mobiles",
        "price": 64999.00,
        "rating": 4.7,
        "description": "Smooth Beyond Belief with 4th Gen Hasselblad Camera, Snapdragon 8 Gen 3, and 100W SUPERVOOC charging.",
        "specifications": {
            "Processor": "Snapdragon 8 Gen 3",
            "RAM": "12GB",
            "Storage": "256GB",
            "Camera": "50MP Hasselblad",
            "Battery": "5400 mAh"
        },
        "image_url": "static/images/products/oneplus_12.jpg",
        "stock_quantity": 30,
        "is_available": True
    },
    {
        "sku": "MOB006",
        "slug": "samsung-galaxy-z-fold-5",
        "name": "Samsung Galaxy Z Fold 5",
        "brand": "Samsung",
        "category_slug": "mobiles",
        "price": 154999.00,
        "rating": 4.6,
        "description": "Unfold a massive 7.6-inch main screen with zero-gap Flex Hinge, taskbar multitasking, and S Pen support.",
        "specifications": {
            "Processor": "Snapdragon 8 Gen 2",
            "RAM": "12GB",
            "Storage": "512GB",
            "Display": "7.6-inch Foldable AMOLED",
            "Battery": "4400 mAh"
        },
        "image_url": "static/images/products/galaxy_z_fold_5.jpg",
        "stock_quantity": 15,
        "is_available": True
    },
    {
        "sku": "MOB007",
        "slug": "xiaomi-14-ultra",
        "name": "Xiaomi 14 Ultra",
        "brand": "Xiaomi",
        "category_slug": "mobiles",
        "price": 99999.00,
        "rating": 4.8,
        "description": "Optical pinnacle co-engineered with Leica featuring 1-inch Sony LYT-900 sensor and stepless variable aperture.",
        "specifications": {
            "Processor": "Snapdragon 8 Gen 3",
            "RAM": "16GB",
            "Storage": "512GB",
            "Camera": "50MP 1-inch Leica Quad Camera",
            "Battery": "5000 mAh"
        },
        "image_url": "static/images/products/xiaomi_14_ultra.jpg",
        "stock_quantity": 18,
        "is_available": True
    },
    {
        "sku": "MOB008",
        "slug": "nothing-phone-2",
        "name": "Nothing Phone (2)",
        "brand": "Nothing",
        "category_slug": "mobiles",
        "price": 37999.00,
        "rating": 4.4,
        "description": "Unique transparent aesthetic featuring Glyph Interface LED lighting, Nothing OS 2.5, and dual 50MP cameras.",
        "specifications": {
            "Processor": "Snapdragon 8+ Gen 1",
            "RAM": "12GB",
            "Storage": "256GB",
            "Camera": "Dual 50MP Camera",
            "Battery": "4700 mAh"
        },
        "image_url": "static/images/products/nothing_phone_2.jpg",
        "stock_quantity": 28,
        "is_available": True
    },
    {
        "sku": "MOB009",
        "slug": "samsung-galaxy-a55-5g",
        "name": "Samsung Galaxy A55 5G",
        "brand": "Samsung",
        "category_slug": "mobiles",
        "price": 39999.00,
        "rating": 4.3,
        "description": "Premium metal frame smartphone with Knox Vault security, IP67 water resistance, and Nightography camera.",
        "specifications": {
            "Processor": "Exynos 1480",
            "RAM": "8GB",
            "Storage": "256GB",
            "Camera": "50MP OIS Main",
            "Battery": "5000 mAh"
        },
        "image_url": "static/images/products/galaxy_a55.jpg",
        "stock_quantity": 50,
        "is_available": True
    },
    {
        "sku": "MOB010",
        "slug": "vivo-x100-pro-5g",
        "name": "Vivo X100 Pro 5G",
        "brand": "Vivo",
        "category_slug": "mobiles",
        "price": 89999.00,
        "rating": 4.7,
        "description": "ZEISS APO Telephoto camera flagship with 1-inch main sensor, V3 imaging chip, and Dimensity 9300 chipset.",
        "specifications": {
            "Processor": "Dimensity 9300",
            "RAM": "16GB",
            "Storage": "512GB",
            "Camera": "50MP ZEISS 1-inch",
            "Battery": "5400 mAh"
        },
        "image_url": "static/images/products/vivo_x100_pro.jpg",
        "stock_quantity": 16,
        "is_available": True
    },
    {
        "sku": "MOB011",
        "slug": "iqoo-12-5g",
        "name": "iQOO 12 5G",
        "brand": "iQOO",
        "category_slug": "mobiles",
        "price": 52999.00,
        "rating": 4.6,
        "description": "Gaming and performance flagship powered by Snapdragon 8 Gen 3, dedicated Q1 Supercomputing Chip, and 144Hz display.",
        "specifications": {
            "Processor": "Snapdragon 8 Gen 3",
            "RAM": "16GB",
            "Storage": "512GB",
            "Camera": "50MP Main + 64MP Periscope",
            "Battery": "5000 mAh"
        },
        "image_url": "static/images/products/iqoo_12.jpg",
        "stock_quantity": 25,
        "is_available": True
    },
    {
        "sku": "MOB012",
        "slug": "realme-gt-5-pro",
        "name": "Realme GT 5 Pro",
        "brand": "Realme",
        "category_slug": "mobiles",
        "price": 46999.00,
        "rating": 4.5,
        "description": "Value flagship packed with Sony IMX890 periscope telephoto camera, Snapdragon 8 Gen 3, and 4500 nits peak brightness.",
        "specifications": {
            "Processor": "Snapdragon 8 Gen 3",
            "RAM": "12GB",
            "Storage": "256GB",
            "Camera": "50MP Periscope Camera",
            "Battery": "5400 mAh"
        },
        "image_url": "static/images/products/realme_gt_5_pro.jpg",
        "stock_quantity": 30,
        "is_available": True
    },
    {
        "sku": "MOB013",
        "slug": "motorola-edge-50-ultra",
        "name": "Motorola Edge 50 Ultra",
        "brand": "Motorola",
        "category_slug": "mobiles",
        "price": 59999.00,
        "rating": 4.5,
        "description": "Real wooden back design smartphone featuring Pantone validated colors, 125W TurboPower charging, and Moto AI.",
        "specifications": {
            "Processor": "Snapdragon 8s Gen 3",
            "RAM": "12GB",
            "Storage": "512GB",
            "Camera": "50MP + 50MP + 64MP",
            "Battery": "4500 mAh"
        },
        "image_url": "static/images/products/moto_edge_50_ultra.jpg",
        "stock_quantity": 20,
        "is_available": True
    },

    # ==========================================
    # 3. HEADPHONES (12 Products)
    # ==========================================
    {
        "sku": "HP001",
        "slug": "sony-wh-1000xm5",
        "name": "Sony WH-1000XM5",
        "brand": "Sony",
        "category_slug": "headphones",
        "price": 29990.00,
        "rating": 4.8,
        "description": "Industry-leading noise canceling with two processors and 8 microphones for unparalleled calls and music audio.",
        "specifications": {
            "Type": "Over-Ear Wireless",
            "Noise Cancellation": "QN1 Processor",
            "Battery Life": "30 Hours",
            "Driver Unit": "30mm"
        },
        "image_url": "static/images/products/sony_wh1000xm5.jpg",
        "stock_quantity": 50,
        "is_available": True
    },
    {
        "sku": "HP002",
        "slug": "bose-quietcomfort-ultra",
        "name": "Bose QuietComfort Ultra",
        "brand": "Bose",
        "category_slug": "headphones",
        "price": 35900.00,
        "rating": 4.7,
        "description": "World-class noise cancellation, spatialized audio, and CustomTune technology for personalized sound.",
        "specifications": {
            "Type": "Over-Ear Wireless",
            "Audio Tech": "Spatial Audio",
            "Battery Life": "24 Hours"
        },
        "image_url": "static/images/products/bose_qc_ultra.jpg",
        "stock_quantity": 35,
        "is_available": True
    },
    {
        "sku": "HP003",
        "slug": "apple-airpods-max",
        "name": "Apple AirPods Max",
        "brand": "Apple",
        "category_slug": "headphones",
        "price": 59900.00,
        "rating": 4.6,
        "description": "Apple-designed dynamic driver provides high-fidelity audio with Computational audio and Active Noise Cancellation.",
        "specifications": {
            "Type": "Over-Ear Wireless",
            "Chip": "Dual Apple H1",
            "Battery Life": "20 Hours"
        },
        "image_url": "static/images/products/airpods_max.jpg",
        "stock_quantity": 15,
        "is_available": True
    },
    {
        "sku": "HP004",
        "slug": "sony-wf-1000xm5",
        "name": "Sony WF-1000XM5",
        "brand": "Sony",
        "category_slug": "headphones",
        "price": 24990.00,
        "rating": 4.7,
        "description": "The best truly wireless noise canceling earbuds with Dynamic Driver X, LDAC Hi-Res Audio, and bone conduction sensors.",
        "specifications": {
            "Type": "In-Ear Earbuds",
            "Noise Cancellation": "V2 Processor",
            "Battery Life": "24 Hours with Case"
        },
        "image_url": "static/images/products/sony_wf1000xm5.jpg",
        "stock_quantity": 40,
        "is_available": True
    },
    {
        "sku": "HP005",
        "slug": "apple-airpods-pro-2nd-gen",
        "name": "Apple AirPods Pro (2nd Gen)",
        "brand": "Apple",
        "category_slug": "headphones",
        "price": 24900.00,
        "rating": 4.8,
        "description": "Up to 2x more Active Noise Cancellation with H2 chip, Adaptive Audio, and USB-C MagSafe Charging Case.",
        "specifications": {
            "Type": "In-Ear Earbuds",
            "Chip": "Apple H2",
            "Battery Life": "30 Hours with Case"
        },
        "image_url": "static/images/products/airpods_pro_2.jpg",
        "stock_quantity": 60,
        "is_available": True
    },
    {
        "sku": "HP006",
        "slug": "sennheiser-momentum-4-wireless",
        "name": "Sennheiser Momentum 4 Wireless",
        "brand": "Sennheiser",
        "category_slug": "headphones",
        "price": 27990.00,
        "rating": 4.6,
        "description": "Unmatched 60-hour battery life with audiophile-inspired 42mm transducer system and customizable Sound Personalization.",
        "specifications": {
            "Type": "Over-Ear Wireless",
            "Driver": "42mm",
            "Battery Life": "60 Hours"
        },
        "image_url": "static/images/products/sennheiser_momentum_4.jpg",
        "stock_quantity": 25,
        "is_available": True
    },
    {
        "sku": "HP007",
        "slug": "jbl-tour-one-m2",
        "name": "JBL Tour One M2",
        "brand": "JBL",
        "category_slug": "headphones",
        "price": 19999.00,
        "rating": 4.4,
        "description": "True Adaptive Noise Cancelling over-ear headphones with Smart Ambient technology and JBL Pro Sound.",
        "specifications": {
            "Type": "Over-Ear Wireless",
            "Driver": "40mm",
            "Battery Life": "50 Hours"
        },
        "image_url": "static/images/products/jbl_tour_one_m2.jpg",
        "stock_quantity": 30,
        "is_available": True
    },
    {
        "sku": "HP008",
        "slug": "beats-studio-pro",
        "name": "Beats Studio Pro",
        "brand": "Beats",
        "category_slug": "headphones",
        "price": 34900.00,
        "rating": 4.5,
        "description": "Fully custom acoustic platform with Lossless Audio via USB-C, ANC, and enhanced Apple and Android compatibility.",
        "specifications": {
            "Type": "Over-Ear Wireless",
            "Audio Tech": "Spatial Audio",
            "Battery Life": "40 Hours"
        },
        "image_url": "static/images/products/beats_studio_pro.jpg",
        "stock_quantity": 20,
        "is_available": True
    },
    {
        "sku": "HP009",
        "slug": "audio-technica-ath-m50xbt2",
        "name": "Audio-Technica ATH-M50xBT2",
        "brand": "Audio-Technica",
        "category_slug": "headphones",
        "price": 18990.00,
        "rating": 4.7,
        "description": "Critically acclaimed studio monitor sound signature converted to wireless with AK4331 DAC and dual beamforming mics.",
        "specifications": {
            "Type": "Studio Monitor Wireless",
            "Driver": "45mm",
            "Battery Life": "50 Hours"
        },
        "image_url": "static/images/products/audio_technica_m50xbt2.jpg",
        "stock_quantity": 18,
        "is_available": True
    },
    {
        "sku": "HP010",
        "slug": "anker-soundcore-space-q45",
        "name": "Anker Soundcore Space Q45",
        "brand": "Anker",
        "category_slug": "headphones",
        "price": 9999.00,
        "rating": 4.5,
        "description": "Best budget ANC headphones with up to 98% noise reduction, LDAC Hi-Res Wireless sound, and 50-hour playtime.",
        "specifications": {
            "Type": "Over-Ear Wireless",
            "Noise Cancellation": "Adaptive ANC",
            "Battery Life": "50 Hours"
        },
        "image_url": "static/images/products/anker_space_q45.jpg",
        "stock_quantity": 40,
        "is_available": True
    },
    {
        "sku": "HP011",
        "slug": "jabra-elite-10",
        "name": "Jabra Elite 10",
        "brand": "Jabra",
        "category_slug": "headphones",
        "price": 19999.00,
        "rating": 4.4,
        "description": "Ultimate Comfort TWS earbuds with Dolby Atmos Spatial Sound, Jabra Advanced ANC, and 6-microphone call clarity.",
        "specifications": {
            "Type": "In-Ear Earbuds",
            "Audio Tech": "Dolby Spatial Sound",
            "Battery Life": "27 Hours with Case"
        },
        "image_url": "static/images/products/jabra_elite_10.jpg",
        "stock_quantity": 22,
        "is_available": True
    },
    {
        "sku": "HP012",
        "slug": "shure-aonic-50-gen-2",
        "name": "Shure AONIC 50 Gen 2",
        "brand": "Shure",
        "category_slug": "headphones",
        "price": 34990.00,
        "rating": 4.6,
        "description": "Studio-quality wireless headphones with customizable spatial audio technology and Snapdragon Sound integration.",
        "specifications": {
            "Type": "Over-Ear Studio Wireless",
            "Driver": "50mm",
            "Battery Life": "45 Hours"
        },
        "image_url": "static/images/products/shure_aonic_50_gen2.jpg",
        "stock_quantity": 12,
        "is_available": True
    },

    # ==========================================
    # 4. SMART WATCHES (12 Products)
    # ==========================================
    {
        "sku": "SW001",
        "slug": "apple-watch-ultra-2",
        "name": "Apple Watch Ultra 2",
        "brand": "Apple",
        "category_slug": "smart-watches",
        "price": 89900.00,
        "rating": 4.9,
        "description": "The ultimate sports and adventure watch with S9 SiP, Double Tap gesture, and 3000 nits display brightness.",
        "specifications": {
            "Case Size": "49mm Titanium",
            "Display": "Retina 3000 nits",
            "Battery Life": "36 Hours"
        },
        "image_url": "static/images/products/apple_watch_ultra_2.jpg",
        "stock_quantity": 20,
        "is_available": True
    },
    {
        "sku": "SW002",
        "slug": "samsung-galaxy-watch-6-classic",
        "name": "Samsung Galaxy Watch 6 Classic",
        "brand": "Samsung",
        "category_slug": "smart-watches",
        "price": 36999.00,
        "rating": 4.6,
        "description": "Iconic rotating bezel returns with 20% larger screen, BioActive Sensor, and advanced sleep coaching.",
        "specifications": {
            "Case Size": "47mm Stainless Steel",
            "Display": "1.5-inch Super AMOLED",
            "OS": "Wear OS"
        },
        "image_url": "static/images/products/galaxy_watch_6_classic.jpg",
        "stock_quantity": 28,
        "is_available": True
    },
    {
        "sku": "SW003",
        "slug": "apple-watch-series-9",
        "name": "Apple Watch Series 9",
        "brand": "Apple",
        "category_slug": "smart-watches",
        "price": 41900.00,
        "rating": 4.7,
        "description": "Smarter, brighter, and mightier smartwatch featuring S9 SiP, magic Double Tap gesture, and Precision Finding.",
        "specifications": {
            "Case Size": "45mm Aluminum",
            "Display": "Always-On Retina",
            "OS": "watchOS 10"
        },
        "image_url": "static/images/products/apple_watch_series_9.jpg",
        "stock_quantity": 35,
        "is_available": True
    },
    {
        "sku": "SW004",
        "slug": "samsung-galaxy-watch-5-pro",
        "name": "Samsung Galaxy Watch 5 Pro",
        "brand": "Samsung",
        "category_slug": "smart-watches",
        "price": 27999.00,
        "rating": 4.5,
        "description": "Designed for outdoor navigators with Titanium body, Route Workout GPX tracking, and massive 590mAh battery.",
        "specifications": {
            "Case Size": "45mm Titanium",
            "Display": "1.4-inch AMOLED",
            "Battery": "590 mAh"
        },
        "image_url": "static/images/products/galaxy_watch_5_pro.jpg",
        "stock_quantity": 22,
        "is_available": True
    },
    {
        "sku": "SW005",
        "slug": "garmin-fenix-7-pro-sapphire-solar",
        "name": "Garmin Fenix 7 Pro Sapphire Solar",
        "brand": "Garmin",
        "category_slug": "smart-watches",
        "price": 81990.00,
        "rating": 4.8,
        "description": "Multisport GPS watch with built-in LED flashlight, Power Sapphire solar charging lens, and endurance score.",
        "specifications": {
            "Case Size": "47mm Titanium",
            "Display": "1.3-inch MIP Solar",
            "Battery Life": "Up to 22 Days"
        },
        "image_url": "static/images/products/garmin_fenix_7_pro.jpg",
        "stock_quantity": 12,
        "is_available": True
    },
    {
        "sku": "SW006",
        "slug": "garmin-forerunner-965",
        "name": "Garmin Forerunner 965",
        "brand": "Garmin",
        "category_slug": "smart-watches",
        "price": 67490.00,
        "rating": 4.7,
        "description": "Premium triathlon and running smartwatch featuring brilliant AMOLED touchscreen display and lightweight titanium bezel.",
        "specifications": {
            "Case Size": "47mm Titanium",
            "Display": "1.4-inch AMOLED",
            "Battery Life": "Up to 23 Days"
        },
        "image_url": "static/images/products/garmin_forerunner_965.jpg",
        "stock_quantity": 15,
        "is_available": True
    },
    {
        "sku": "SW007",
        "slug": "google-pixel-watch-2",
        "name": "Google Pixel Watch 2",
        "brand": "Google",
        "category_slug": "smart-watches",
        "price": 39900.00,
        "rating": 4.4,
        "description": "Help by Google, health by Fitbit. All-new quad-core CPU, multi-path heart rate sensor, and Safety Check feature.",
        "specifications": {
            "Case Size": "41mm Aluminum",
            "Display": "3D Gorilla Glass 5",
            "OS": "Wear OS 4"
        },
        "image_url": "static/images/products/pixel_watch_2.jpg",
        "stock_quantity": 25,
        "is_available": True
    },
    {
        "sku": "SW008",
        "slug": "fitbit-sense-2",
        "name": "Fitbit Sense 2",
        "brand": "Fitbit",
        "category_slug": "smart-watches",
        "price": 20999.00,
        "rating": 4.3,
        "description": "Advanced health and fitness watch designed to help manage stress, track sleep, and monitor heart health.",
        "specifications": {
            "Display": "Color AMOLED",
            "Battery Life": "6+ Days",
            "Sensors": "cEDA Stress, ECG"
        },
        "image_url": "static/images/products/fitbit_sense_2.jpg",
        "stock_quantity": 30,
        "is_available": True
    },
    {
        "sku": "SW009",
        "slug": "amazfit-t-rex-2",
        "name": "Amazfit T-Rex 2",
        "brand": "Amazfit",
        "category_slug": "smart-watches",
        "price": 15999.00,
        "rating": 4.5,
        "description": "Rugged outdoor GPS smartwatch passed 15 military-grade tests with ultra-low temperature operation.",
        "specifications": {
            "Case Size": "47.1mm Polymer",
            "Display": "1.39-inch AMOLED",
            "Battery Life": "24 Days"
        },
        "image_url": "static/images/products/amazfit_trex_2.jpg",
        "stock_quantity": 40,
        "is_available": True
    },
    {
        "sku": "SW010",
        "slug": "oneplus-watch-2",
        "name": "OnePlus Watch 2",
        "brand": "OnePlus",
        "category_slug": "smart-watches",
        "price": 24999.00,
        "rating": 4.6,
        "description": "Dual-Engine Architecture with Snapdragon W5 + BES2700 chipsets delivering up to 100 hours of battery life in Smart Mode.",
        "specifications": {
            "Case Size": "47mm Stainless Steel",
            "Display": "1.43-inch AMOLED",
            "Battery": "500 mAh"
        },
        "image_url": "static/images/products/oneplus_watch_2.jpg",
        "stock_quantity": 25,
        "is_available": True
    },
    {
        "sku": "SW011",
        "slug": "xiaomi-watch-2-pro",
        "name": "Xiaomi Watch 2 Pro",
        "brand": "Xiaomi",
        "category_slug": "smart-watches",
        "price": 19999.00,
        "rating": 4.4,
        "description": "Smart watch powered by Snapdragon W5+ Gen 1 platform, Google Wear OS, and bioelectrical impedance body composition sensor.",
        "specifications": {
            "Case Size": "46mm Stainless Steel",
            "Display": "1.43-inch AMOLED",
            "OS": "Wear OS"
        },
        "image_url": "static/images/products/xiaomi_watch_2_pro.jpg",
        "stock_quantity": 30,
        "is_available": True
    },
    {
        "sku": "SW012",
        "slug": "fossil-gen-6-smartwatch",
        "name": "Fossil Gen 6 Smartwatch",
        "brand": "Fossil",
        "category_slug": "smart-watches",
        "price": 18495.00,
        "rating": 4.2,
        "description": "Classic watch aesthetic paired with Wear OS, fast charging (80% in 30 mins), and SpO2 sensor.",
        "specifications": {
            "Case Size": "44mm Stainless Steel",
            "Display": "1.28-inch Color AMOLED",
            "OS": "Wear OS"
        },
        "image_url": "static/images/products/fossil_gen_6.jpg",
        "stock_quantity": 18,
        "is_available": True
    }
]


def seed_database(app=None):
    """
    Idempotent Database Seeding Function:
    Checks existing records before insertion to guarantee no duplicate entries.
    """
    if app is None:
        app = create_app()

    with app.app_context():
        print("\n==================================================")
        print("SEEDING AI SHOPPING ASSISTANT DATABASE")
        print("==================================================")

        # 1. Ensure database tables exist
        db.create_all()

        # Idempotency Check: If database is already populated, skip seeding
        existing_categories_count = Category.query.count()
        existing_products_count = Product.query.count()

        if existing_categories_count >= len(CATEGORIES_DATA) and existing_products_count >= len(PRODUCTS_DATA):
            print("\nDatabase already seeded.")
            print(f"Current Record Totals: {existing_categories_count} Categories, {existing_products_count} Products.")
            print("==================================================\n")
            return

        # 2. Seed Categories
        print("\n[1/3] Seeding Categories...")
        category_map = {}
        for cat_data in CATEGORIES_DATA:
            category = Category.query.filter_by(slug=cat_data["slug"]).first()
            if not category:
                category = Category(
                    name=cat_data["name"],
                    slug=cat_data["slug"],
                    description=cat_data["description"]
                )
                db.session.add(category)
                db.session.flush()
                print(f"  + Added Category: {cat_data['name']}")
            else:
                print(f"  . Category already exists: {cat_data['name']}")
            category_map[cat_data["slug"]] = category.id

        db.session.commit()

        # 3. Seed Default Users
        print("\n[2/3] Seeding Default Users...")
        demo_users = [
            {
                "username": "admin",
                "email": "admin@aishopping.com",
                "password_hash": generate_password_hash("Admin@12345"),
                "first_name": "System",
                "last_name": "Admin",
                "role": UserRole.ADMIN,
                "email_verified": True
            },
            {
                "username": "demouser",
                "email": "user@aishopping.com",
                "password_hash": generate_password_hash("User@12345"),
                "first_name": "John",
                "last_name": "Doe",
                "role": UserRole.USER,
                "email_verified": True
            }
        ]

        for user_info in demo_users:
            existing_user = User.query.filter_by(username=user_info["username"]).first()
            if not existing_user:
                u = User(**user_info)
                db.session.add(u)
                print(f"  + Added User: {user_info['username']} ({user_info['role'].value})")
            else:
                print(f"  . User already exists: {user_info['username']}")

        db.session.commit()

        # 4. Seed Products
        print("\n[3/3] Seeding Sample Products...")
        added_count = 0
        skipped_count = 0

        for prod_data in PRODUCTS_DATA:
            slug_cat = prod_data.pop("category_slug")
            cat_id = category_map.get(slug_cat)

            existing_prod = Product.query.filter_by(sku=prod_data["sku"]).first()
            if not existing_prod:
                prod = Product(
                    sku=prod_data["sku"],
                    slug=prod_data["slug"],
                    name=prod_data["name"],
                    brand=prod_data["brand"],
                    category_id=cat_id,
                    price=prod_data["price"],
                    rating=prod_data["rating"],
                    description=prod_data["description"],
                    specifications=prod_data["specifications"],
                    image_url=prod_data["image_url"],
                    stock_quantity=prod_data["stock_quantity"],
                    is_available=prod_data.get("is_available", True),
                    is_active=True
                )
                db.session.add(prod)
                added_count += 1
            else:
                skipped_count += 1

            # Restore category_slug for subsequent idempotency checks
            prod_data["category_slug"] = slug_cat

        db.session.commit()

        print(f"\n  [OK] Seeded {added_count} new products.")
        if skipped_count > 0:
            print(f"  . Skipped {skipped_count} existing products.")

        # Final Summary
        total_users = User.query.count()
        total_categories = Category.query.count()
        total_products = Product.query.count()

        print("\n==================================================")
        print("DATABASE SEEDING COMPLETED SUCCESSFULLY!")
        print("==================================================")
        print(f"  * Total Categories in DB : {total_categories}")
        print(f"  * Total Users in DB      : {total_users}")
        print(f"  * Total Products in DB   : {total_products}")
        print("==================================================\n")


if __name__ == "__main__":
    seed_database()
