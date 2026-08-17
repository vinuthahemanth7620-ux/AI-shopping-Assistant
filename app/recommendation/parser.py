import re
import logging
from sqlalchemy import func
from app import db

logger = logging.getLogger(__name__)

USD_TO_INR = 83.0


class RequirementParser:
    """
    Requirement Parser - Natural Language Requirement Extraction Layer.
    Parses unstructured user query text into structured shopping intent:
    - product_intent (primary entity requested: toys, makeup, laptop, induction stove, etc.)
    - category_family (beauty, electronics, kitchen, fashion, home, toys, sports, etc.)
    - category_ids (MySQL Category IDs)
    - max_price / min_price (in INR)
    - min_rating
    - quality_preference
    - brand
    - feature_keywords
    - sort_preference
    - is_primary_request / is_accessory_request
    - is_conversation / conversational_intent ('greeting', 'help', 'gratitude', 'goodbye')
    """

    # Comprehensive Category Taxonomy covering all 39 MySQL database categories
    CATEGORY_TAXONOMY = {
        'video_games': {
            'cat_ids': [39, 20, 7],  # 39: Video Games, 20: Computers, 7: All Electronics
            'family': 'gaming',
            'primary_terms': [
                'video game', 'video games', 'gaming', 'gamer', 'playstation', 'ps5', 'ps4',
                'xbox', 'xbox series x', 'nintendo', 'nintendo switch', 'gaming console',
                'retro game console', 'gamepad', 'controller', 'joystick', 'gaming headset',
                'gaming keyboard', 'gaming mouse', 'rtx', 'gpu', 'gaming laptop'
            ],
            'disqualifying_accessories': ['door lock', 'caulking', 'cylinder']
        },
        'toys_games': {
            'cat_ids': [38, 39],  # 38: Toys & Games, 39: Video Games
            'family': 'toys',
            'primary_terms': [
                'toy', 'toys', 'kids toy', 'kids toys', 'board game', 'board games',
                'puzzle', 'puzzles', 'jigsaw', 'action figure', 'action figures', 'doll', 'dolls',
                'dollhouse', 'lego', 'building block', 'building blocks', 'building set', 'rc car',
                'remote control car', 'diecast', 'drone toy', 'slime', 'playdough', 'card game',
                'playing cards', 'fidget toy', 'frisbee', 'party game', 'educational toy', 'stuffed animal',
                'plush toy', 'toy gun', 'water gun', 'nerf', 'toy car', 'toy train', 'model train',
                'barbie', 'hot wheels', 'beyblade', 'yo-yo', 'play set', 'playset'
            ],
            'disqualifying_accessories': [
                'battery adapter', 'dewalt', 'catnip', 'pet toy', 'chew toy', 'hamster', 'screen protector',
                'phone case', 'screwdriver', 'faucet', 'condiment'
            ]
        },
        'baby': {
            'cat_ids': [14, 5, 38],  # 14: Baby, 5: AMAZON FASHION, 38: Toys & Games
            'family': 'baby',
            'primary_terms': [
                'baby', 'infant', 'newborn', 'toddler', 'baby clothes', 'baby bib', 'baby bibs',
                'baby romper', 'baby blanket', 'baby bottle', 'pacifier', 'stroller', 'pram',
                'diaper', 'diapers', 'baby wipes', 'crib', 'baby carrier', 'baby monitor', 'baby bath',
                'baby toy', 'baby toys', 'teether', 'high chair', 'swaddle'
            ],
            'disqualifying_accessories': [
                'battery adapter', 'screen protector', 'car cover', 'drill'
            ]
        },
        'pet_supplies': {
            'cat_ids': [32],  # 32: Pet Supplies
            'family': 'pet',
            'primary_terms': [
                'pet', 'pets', 'pet supplies', 'dog', 'dogs', 'puppy', 'cat', 'cats', 'kitten',
                'cat food', 'dog food', 'pet food', 'cat treats', 'dog treats', 'catnip', 'cat toy',
                'dog toy', 'pet bed', 'dog leash', 'pet collar', 'pet harness', 'litter box',
                'cat tree', 'scratching post', 'aquarium', 'fish food', 'bird cage', 'dog bowl', 'pet shampoo'
            ],
            'disqualifying_accessories': [
                'condiment container', 'faucet', 'power wheels', 'dewalt'
            ]
        },
        'sports_outdoors': {
            'cat_ids': [35, 5],  # 35: Sports & Outdoors, 5: AMAZON FASHION
            'family': 'sports',
            'primary_terms': [
                'sport', 'sports', 'outdoors', 'fitness', 'gym', 'workout', 'exercise', 'yoga',
                'yoga mat', 'dumbbell', 'dumbbells', 'resistance band', 'resistance bands', 'treadmill',
                'exercise bike', 'running shoe', 'running shoes', 'athletic shoe', 'athletic shoes',
                'football', 'soccer', 'basketball', 'cricket', 'badminton', 'tennis', 'racket',
                'cycling', 'helmet', 'camping', 'tent', 'sleeping bag', 'hiking', 'trekking', 'sports equipment'
            ],
            'disqualifying_accessories': [
                'controller board', 'rectangula', 'faucet', 'battery adapter'
            ]
        },
        'automotive': {
            'cat_ids': [13, 16],  # 13: Automotive, 16: Car Electronics
            'family': 'automotive',
            'primary_terms': [
                'automotive', 'car', 'cars', 'auto', 'vehicle', 'car accessories', 'car accessory',
                'car interior', 'car seat cover', 'car cover', 'car floor mat', 'dash cam',
                'car charger', 'car phone mount', 'car cleaning', 'car vacuum', 'tire inflator',
                'wiper', 'key fob cover', 'motorcycle', 'bike accessories', 'jump starter'
            ],
            'disqualifying_accessories': [
                'rhinestone brooch', 'dress', 't-shirt', 'earrings'
            ]
        },
        'arts_and_crafts': {
            'cat_ids': [12, 26],  # 12: Arts, Crafts & Sewing, 26: Handmade
            'family': 'crafts',
            'primary_terms': [
                'craft', 'crafts', 'crafting', 'art', 'arts', 'sewing', 'sewing machine', 'knitting',
                'embroidery', 'paint', 'painting', 'acrylic paint', 'watercolor', 'paint brush',
                'canvas', 'yarn', 'beads', 'diamond painting', 'glue gun', 'origami', 'sketchbook',
                'markers', 'crayons', 'colored pencils', 'craft kit', 'needlework', 'ribbon'
            ],
            'disqualifying_accessories': [
                'dewalt', 'battery adapter', 'faucet', 'engine'
            ]
        },
        'grocery': {
            'cat_ids': [25],  # 25: Grocery
            'family': 'grocery',
            'primary_terms': [
                'grocery', 'groceries', 'food', 'snack', 'snacks', 'pantry', 'beverage', 'beverages',
                'tea', 'coffee', 'coffee beans', 'creamer', 'biscuits', 'cookies', 'chocolate',
                'cereal', 'honey', 'nuts', 'dry fruits', 'spices', 'cooking oil', 'pasta', 'sauce',
                'noodles', 'energy bar', 'protein powder', 'healthy snack'
            ],
            'disqualifying_accessories': [
                'condiment container', 'kitchen faucet', 'battery adapter'
            ]
        },
        'musical_instruments': {
            'cat_ids': [30, 28],  # 30: Musical Instruments, 28: Home Audio
            'family': 'music',
            'primary_terms': [
                'musical instrument', 'musical instruments', 'music', 'instrument', 'instruments',
                'guitar', 'acoustic guitar', 'electric guitar', 'ukulele', 'keyboard piano',
                'digital piano', 'drums', 'drum set', 'flute', 'violin', 'trumpet', 'saxophone',
                'kazoo', 'kazoos', 'harmonica', 'microphone', 'mic', 'guitar strings', 'tuner',
                'metronome', 'shaker', 'egg shaker'
            ],
            'disqualifying_accessories': [
                'battery adapter', 'screwdriver', 'faucet'
            ]
        },
        'office_products': {
            'cat_ids': [31, 20],  # 31: Office Products, 20: Computers
            'family': 'office',
            'primary_terms': [
                'office', 'office products', 'stationery', 'stationery items', 'office chair',
                'desk chair', 'ergonomic chair', 'study table', 'whiteboard', 'bulletin board',
                'planner', 'notebook', 'notebooks', 'journal', 'diary', 'pen', 'pens', 'pencil',
                'stapler', 'paper', 'printer paper', 'file folder', 'desk organizer', 'printer'
            ],
            'disqualifying_accessories': [
                'bed frame', 'volleyball', 'dewalt'
            ]
        },
        'fashion': {
            'cat_ids': [5, 35],  # 5: AMAZON FASHION, 35: Sports & Outdoors
            'family': 'fashion',
            'primary_terms': [
                'clothing', 'clothes', 'apparel', 'dress', 'dresses', 'shirt', 'shirts', 't-shirt',
                't-shirts', 'tshirt', 'tshirts', 'top', 'tops', 'jeans', 'pants', 'trousers',
                'hoodie', 'hoodies', 'sweater', 'jacket', 'jackets', 'coat', 'suit', 'saree',
                'kurti', 'skirt', 'shorts', 'leggings', 'sportswear', 'activewear', 'fashion',
                'outfit', 'underwear', 'socks', 'fashion jewelry', 'necklace', 'earrings', 'bracelet',
                'handbag', 'purse', 'wallet'
            ],
            'disqualifying_accessories': [
                'battery adapter', 'dewalt', 'faucet', 'drill'
            ]
        },
        'beauty': {
            'cat_ids': [6, 27, 5],  # 6: All Beauty, 27: Health & Personal Care, 5: AMAZON FASHION
            'family': 'beauty',
            'primary_terms': [
                'makeup', 'cosmetics', 'cosmetic', 'beauty', 'beauty products', 'beauty item', 'beauty items',
                'makeup items', 'makeup product', 'makeup products', 'makeup kit', 'makeup brush', 'eyeshadow',
                'palette', 'lipstick', 'foundation', 'mascara', 'eyeliner', 'blush', 'concealer', 'compact powder',
                'nail polish', 'nail art', 'nail decals', 'nail charms', 'eyelash', 'epilator',
                'hair curler', 'hair eraser', 'face massager', 'gua sha', 'beauty blender', 'fake eyelash'
            ],
            'disqualifying_accessories': [
                'refrigerator', 'mini fridge', 'stove', 'cooktop', 'microwave', 'oven', 'vanity table',
                'bed frame', 'screwdriver', 'flag', 'volleyball', 'vacuum', 'dishwasher', 'laptop',
                'headphone', 'phone', 'tumbler', 'coffee mug', 'straw cup', 'teacher gift'
            ]
        },
        'lipstick': {
            'cat_ids': [6, 27, 5],
            'family': 'beauty',
            'primary_terms': [
                'lipstick', 'lip stick', 'lip gloss', 'lip balm', 'lip color', 'lip tint', 'lip liner'
            ],
            'disqualifying_accessories': [
                'refrigerator', 'bed frame', 'straw cup', 'tumbler', 'volleyball', 'flag', 'vanity'
            ]
        },
        'skincare': {
            'cat_ids': [6, 27, 5],
            'family': 'beauty',
            'primary_terms': [
                'skincare', 'skin care', 'face wash', 'facial cream', 'moisturizer', 'cleanser', 'sunscreen',
                'serum', 'face towel', 'dry wipes', 'gua sha', 'body lotion', 'face massager', 'epilator', 'face mask'
            ],
            'disqualifying_accessories': [
                'mini fridge', 'refrigerator', 'stove', 'cooktop', 'laptop', 'screwdriver', 'bed frame'
            ]
        },
        'haircare': {
            'cat_ids': [6, 27, 5],
            'family': 'beauty',
            'primary_terms': [
                'haircare', 'hair care', 'shampoo', 'conditioner', 'hair oil', 'hair curler', 'hair eraser',
                'hair regrowth', 'head shaver', 'hair bonnet', 'sweatband', 'headband', 'hair dryer'
            ],
            'disqualifying_accessories': [
                'refrigerator', 'stove', 'cooktop', 'laptop', 'screwdriver', 'bed frame'
            ]
        },
        'cooktop': {
            'cat_ids': [10],  # 10: Appliances
            'family': 'kitchen',
            'primary_terms': [
                'induction stove', 'induction cooktop', 'induction cooker', 'induction hob',
                'induction burner', 'electric cooktop', 'electric stove', 'cooktop',
                'gas stove', 'stove top', 'hot plate', 'cooker'
            ],
            'disqualifying_accessories': [
                'knob', 'knobs', 'cover', 'covers', 'protector', 'protectors', 'cleaning', 'mat', 'pad', 'cord',
                'organizer', 'rack', 'holder', 'stand', 'pan', 'pot', 'spatula', 'spoon', 'towel', 'cleaner',
                'liner', 'liners', 'light', 'bulb', 'handle', 'refrigerator', 'vanity', 'screwdriver', 'adapter'
            ]
        },
        'kitchen_appliance': {
            'cat_ids': [10, 9],
            'family': 'kitchen',
            'primary_terms': [
                'kitchen appliance', 'kitchen appliances', 'home appliance', 'appliances',
                'mixer', 'grinder', 'blender', 'microwave', 'oven', 'air fryer', 'toaster', 'kettle', 'cooker',
                'refrigerator', 'fridge', 'dishwasher', 'juicer', 'food processor', 'electric kettle'
            ],
            'disqualifying_accessories': [
                'door lock', 'screwdriver', 'laptop', 'phone case', 'flag', 'bed frame'
            ]
        },
        'mixer_grinder': {
            'cat_ids': [10],
            'family': 'kitchen',
            'primary_terms': [
                'mixer', 'grinder', 'mixer grinder', 'blender', 'juicer', 'food processor',
                'hand blender', 'electric blender', 'chopper'
            ],
            'disqualifying_accessories': [
                'replacement blade', 'jar lid', 'gasket', 'ring', 'pestle', 'nail grinder',
                'pet grinder', 'dust cover', 'mat', 'organizer'
            ]
        },
        'washing_machine': {
            'cat_ids': [10],
            'family': 'kitchen',
            'primary_terms': [
                'washing machine', 'washer', 'laundry machine', 'clothes washer', 'dryer', 'spin dryer'
            ],
            'disqualifying_accessories': [
                'hose', 'pipe', 'cover', 'inlet pipe', 'drain hose', 'cleaner', 'tablet',
                'vibration pad', 'foot pad', 'door lock', 'lint filter', 'pet hair remover'
            ]
        },
        'microwave': {
            'cat_ids': [10],
            'family': 'kitchen',
            'primary_terms': [
                'microwave', 'microwave oven', 'oven', 'air fryer', 'toaster oven', 'convection oven'
            ],
            'disqualifying_accessories': [
                'glass plate', 'turntable', 'cover', 'rack', 'light bulb', 'fuse', 'handle'
            ]
        },
        'office_chair': {
            'cat_ids': [9, 31],  # 9: Amazon Home, 31: Office Products
            'family': 'home',
            'primary_terms': [
                'office chair', 'desk chair', 'ergonomic chair', 'swivel chair',
                'gaming chair', 'executive chair', 'patio chair', 'rocking chair', 'recliner'
            ],
            'disqualifying_accessories': [
                'chair cover', 'seat cushion', 'cushion', 'wheel', 'caster', 'armrest cover',
                'slipcover', 'chair mat', 'chair pad', 'footrest', 'chair leg caps'
            ]
        },
        'laptop': {
            'cat_ids': [1, 20],  # 1: Laptops, 20: Computers
            'family': 'electronics',
            'primary_terms': [
                'laptop', 'laptops', 'notebook', 'notebooks', 'macbook', 'chromebook',
                'ultrabook', 'thinkpad', 'ideapad', 'pavilion', 'aspire', 'legion',
                'zenbook', 'vivobook', 'inspiron', 'latitude', 'convertible', 'xps',
                'zephyrus', 'surface pro', 'computer for coding', 'laptop for coding'
            ],
            'disqualifying_accessories': [
                'charger', 'adapter', 'power cord', 'power cable', 'mouse pad', 'mousepad',
                'mouse', 'mice', 'keyboard', 'mat', 'desk pad', 'laptop bag', 'laptop backpack',
                'laptop sleeve', 'laptop case', 'laptop skin', 'laptop stand', 'laptop holder',
                'laptop charger', 'power adapter', 'laptop cable', 'screen protector',
                'keyboard cover', 'docking station', 'usb hub', 'cooling pad', 'ram compatible',
                'memory module for', 'memory upgrade for', 'screen replacement', 'battery replacement',
                'decal sticker', 'mount holder', 'case cover', 'hard case', 'protective case'
            ]
        },
        'mobile': {
            'cat_ids': [2, 17],  # 2: Mobiles, 17: Cell Phones & Accessories
            'family': 'electronics',
            'primary_terms': [
                'phone', 'phones', 'mobile', 'mobiles', 'smartphone', 'smartphones',
                'cellphone', 'cellphones', 'iphone', 'galaxy', 'pixel', 'redmi', 'oneplus', 'android', 'mobile phone'
            ],
            'disqualifying_accessories': [
                'phone case', 'phone cover', 'screen protector', 'tempered glass', 'phone charger',
                'charging cable', 'phone holder', 'car mount', 'phone mount', 'lanyard',
                'replacement battery', 'repair kit', 'stylus pen', 'phone skin', 'wallet case',
                'holster', 'ring holder', 'selfie stick', 'adapter converter', 'camera bracket',
                'adapter bracket', 'portable charger', 'power bank', 'phone grip', 'magnetic phone grip'
            ]
        },
        'headphone': {
            'cat_ids': [3, 28, 33, 17],  # 3: Headphones, 28: Home Audio, 33: Portable Audio
            'family': 'electronics',
            'primary_terms': [
                'headphone', 'headphones', 'earphone', 'earphones', 'earbud', 'earbuds',
                'headset', 'headsets', 'airpods', 'aonic', 'soundcore', 'bose quietcomfort', 'sennheiser'
            ],
            'disqualifying_accessories': [
                'headphone case', 'headphone cover', 'headphone stand', 'headphone holder',
                'headphone hanger', 'eartips', 'ear pads', 'headphone cushion', 'headphone cable',
                'replacement cable', 'upgraded cable', 'earphone cable', 'audio cable',
                'audio adapter', 'headphone amp', 'headphone amplifier', 'dust plug', 'cleaner kit',
                'charging station', 'charging dock', 'headset stand', 'charger', 'solar charger',
                'solar panel', 'dock station', 'controller charger', 'silicone case', 'protective cover',
                'case for airpods', 'cover for airpods', 'keychain', 'skin design'
            ]
        },
        'watch': {
            'cat_ids': [4, 5, 7],  # 4: Smart Watches, 5: Fashion, 7: Electronics
            'family': 'electronics',
            'primary_terms': [
                'smartwatch', 'smartwatches', 'smart watch', 'smart watches', 'fitbit', 'timepiece',
                'chronograph', 'wrist watch', 'wristwatch', 'iwatch'
            ],
            'disqualifying_accessories': [
                'watch band', 'watch strap', 'watchband', 'watch bezel', 'screen protector',
                'watch charger', 'charging cable', 'watch case', 'watch stand', 'watch winder'
            ]
        },
        'shoe': {
            'cat_ids': [5, 35],  # 5: AMAZON FASHION, 35: Sports & Outdoors
            'family': 'fashion',
            'primary_terms': [
                'running shoe', 'running shoes', 'athletic shoe', 'athletic shoes',
                'jogging shoe', 'walking shoe', 'sneaker', 'sneakers', 'shoe', 'shoes', 'footwear'
            ],
            'disqualifying_accessories': [
                'necklace', 'pendant', 'ring', 'earrings', 'jewelry', 't-shirt', 'shirt', 'pants',
                'socks', 'shoelace', 'insole', 'shoe horn', 'shoe tree', 'shoe polish', 'cleaner',
                'shoe bag', 'towel', 'keychain', 'charm', 'cosplay costume', 'sandal', 'sandals',
                'slipper', 'slippers', 'pump', 'heels', 'high heel', 'boot', 'boots', 'ankle boot'
            ]
        },
        'camera': {
            'cat_ids': [15],  # 15: Camera & Photo
            'family': 'electronics',
            'primary_terms': [
                'camera', 'cameras', 'dslr', 'camcorder', 'action camera', 'dash cam',
                'mirrorless camera', 'digital camera', 'vlogging camera'
            ],
            'disqualifying_accessories': [
                'backdrop', 'background', 'camera bag', 'camera case', 'camera strap', 'tripod',
                'monopod', 'camera lens', 'lens filter', 'cleaning kit', 'camera battery',
                'camera charger', 'sd card', 'memory card', 'camera mount', 'camera bracket'
            ]
        },
        'tools_home_improvement': {
            'cat_ids': [37],  # 37: Tools & Home Improvement
            'family': 'tools',
            'primary_terms': [
                'tool', 'tools', 'power tool', 'power tools', 'drill', 'cordless drill',
                'screwdriver', 'screwdriver set', 'wrench', 'hammer', 'pliers', 'tape measure',
                'saw', 'soldering iron', 'hardware', 'plumbing', 'faucet', 'flashlight', 'ladder',
                'toolkit', 'tool set'
            ],
            'disqualifying_accessories': [
                'dress', 'rhinestone', 'cat food'
            ]
        }
    }

    ACCESSORY_ROUTING = {
        'mouse': {
            'target_terms': ['mouse', 'mice'],
            'cat_ids': [20, 7],
            'disqualifying_devices': ['laptop computer', 'notebook computer', 'desktop pc']
        },
        'bag': {
            'target_terms': ['laptop bag', 'laptop backpack', 'laptop sleeve', 'laptop case', 'bag', 'backpack', 'sleeve'],
            'cat_ids': [20, 5, 31],
            'disqualifying_devices': ['laptop computer', 'notebook computer']
        },
        'tripod': {
            'target_terms': ['tripod', 'tripods', 'monopod', 'monopods'],
            'cat_ids': [15],
            'disqualifying_devices': ['digital camera', 'dslr camera', 'camcorder']
        },
        'case': {
            'target_terms': ['phone case', 'phone cover', 'iphone case', 'galaxy case', 'case', 'cover'],
            'cat_ids': [17, 20],
            'disqualifying_devices': ['smartphone', 'cell phone', 'mobile phone']
        }
    }

    COMMON_BRANDS = [
        'Apple', 'Samsung', 'Dell', 'HP', 'Lenovo', 'Asus', 'Acer', 'Sony', 'Bose', 'Sennheiser',
        'Nike', 'Adidas', 'Puma', 'Reebok', 'Under Armour', 'LG', 'Whirlpool', 'Panasonic', 'Philips',
        'Prestige', 'Bajaj', 'Hawkins', 'Pigeon', 'Wonderchef', 'Butterfly', 'Singer', 'Bosch', 'IFB',
        'Haier', 'Godrej', 'OnePlus', 'Xiaomi', 'Redmi', 'Realme', 'Vivo', 'Oppo', 'Motorola', 'Google',
        'Nikon', 'Canon', 'Fujifilm', 'GoPro', 'Fitbit', 'Garmin', 'Boat', 'Noise', 'Fire-Boltt', 'Zebronics',
        'Maybelline', 'L\'Oreal', 'Lakme', 'Nivea', 'Neutrogena', 'Cetaphil', 'Minimalist', 'Plum',
        'LEGO', 'Hasbro', 'Mattel', 'Hot Wheels', 'Barbie', 'Bandai', 'Nerf', 'Fisher-Price', 'Funskool'
    ]

    _BRANDS_CACHE = None

    @classmethod
    def get_cached_brands(cls):
        """Cache active product brands for fast matching."""
        if cls._BRANDS_CACHE is None:
            cls._BRANDS_CACHE = list(cls.COMMON_BRANDS)
            try:
                from app.models.product import Product
                b_rows = db.session.query(Product.brand).filter(Product.is_active == True).limit(200).all()
                for b in b_rows:
                    if b[0] and len(b[0]) >= 2 and b[0] not in cls._BRANDS_CACHE:
                        cls._BRANDS_CACHE.append(b[0])
            except Exception as e:
                logger.error(f"Error caching brands: {str(e)}")
        return cls._BRANDS_CACHE

    @classmethod
    def extract_requirements(cls, query_text, conversation_history=None):
        """
        Extract structured shopping query intent from natural language query string.
        """
        q_raw = query_text.strip()
        q_clean = q_raw.lower()

        req = {
            'original_query': q_raw,
            'product_intent': None,
            'product_type': None,
            'category_family': None,
            'use_case': None,
            'category_ids': [],
            'max_price': None,
            'min_price': None,
            'min_rating': None,
            'quality_preference': 'standard',
            'brand': None,
            'feature_keywords': [],
            'attributes': [],
            'sort_preference': 'recommended',
            'requested_limit': 3,
            'is_primary_request': True,
            'is_accessory_request': False,
            'target_accessory': None,
            'is_followup': False,
            'is_conversation': False,
            'conversational_intent': None
        }

        # 0. Conversational Intent Filter (greetings, help, thanks, goodbye)
        greeting_patterns = [r'^(hi|hello|hey|greetings|good morning|good afternoon|good evening|howdy|namaste)\b', r'^hi\b', r'^hello\b']
        help_patterns = [r'\b(help|help me|what can you do|how to use|who are you|what do you do|features)\b']
        thanks_patterns = [r'\b(thank you|thanks|thank u|thx|appreciate it)\b']
        bye_patterns = [r'\b(bye|goodbye|see you|cya|exit)\b']

        if any(re.search(p, q_clean) for p in greeting_patterns) and len(q_clean.split()) <= 4:
            req['is_conversation'] = True
            req['conversational_intent'] = 'greeting'
            return req
        elif any(re.search(p, q_clean) for p in help_patterns) and len(q_clean.split()) <= 6:
            req['is_conversation'] = True
            req['conversational_intent'] = 'help'
            return req
        elif any(re.search(p, q_clean) for p in thanks_patterns) and len(q_clean.split()) <= 4:
            req['is_conversation'] = True
            req['conversational_intent'] = 'gratitude'
            return req
        elif any(re.search(p, q_clean) for p in bye_patterns) and len(q_clean.split()) <= 3:
            req['is_conversation'] = True
            req['conversational_intent'] = 'goodbye'
            return req

        # Check requested limit (e.g. "show me 5", "top 5")
        limit_match = re.search(r'\b(top|show|give|find|recommend)?\s*([3-5])\b', q_clean)
        if limit_match:
            try:
                req['requested_limit'] = int(limit_match.group(2))
            except ValueError:
                pass

        # 1. Parse tokens & feature keywords
        stop_words = {
            'i', 'need', 'show', 'me', 'find', 'suggest', 'give', 'a', 'an', 'the', 'for', 'with',
            'under', 'below', 'less', 'than', 'between', 'and', 'my', 'best', 'good', 'top', 'rated',
            'highly', 'which', 'what', 'product', 'products', 'something', 'one', 'items', 'item',
            'recommend', 'looking', 'want', 'please', 'can', 'you', 'have', 'do', 'in', 'of', 'on', 'at',
            'buy', 'now', 'planning', 'to', 'some', 'things', 'doing', 'getting', 'ready', 'kit', 'options'
        }
        tokens = [w for w in re.findall(r'\b[a-z0-9]+\b', q_clean) if len(w) >= 2]
        req['feature_keywords'] = [w for w in tokens if w not in stop_words]

        # 2. Check explicit accessory triggers
        accessory_triggers = {
            'mouse': [r'\bmouse\b', r'\bmice\b'],
            'bag': [r'\blaptop bag\b', r'\blaptop backpack\b', r'\blaptop sleeve\b', r'\bbag for laptop\b'],
            'tripod': [r'\btripod\b', r'\bmonopod\b', r'\bcamera tripod\b'],
            'case': [r'\bphone case\b', r'\bphone cover\b', r'\bcase for phone\b', r'\bcover for phone\b']
        }
        for acc_type, patterns in accessory_triggers.items():
            if any(re.search(pat, q_clean) for pat in patterns):
                req['is_accessory_request'] = True
                req['is_primary_request'] = False
                req['target_accessory'] = acc_type
                break

        # 3. Detect Price / Budget Constraints ONLY when explicitly specified
        range_match = re.search(r'between\s*₹?\s*(\d+(?:,\d+)*(?:\.\d+)?k?)\s*and\s*₹?\s*(\d+(?:,\d+)*(?:\.\d+)?k?)', q_clean)
        if range_match:
            min_v = cls._parse_number(range_match.group(1))
            max_v = cls._parse_number(range_match.group(2))
            if min_v and max_v:
                req['min_price'] = min_v
                req['max_price'] = max_v

        if req['max_price'] is None:
            budget_keywords = ['under', 'below', 'less than', 'within', 'max', 'up to', 'budget', 'around', 'spend', 'rs', 'rupees', 'inr', '₹']
            if any(bk in q_clean for bk in budget_keywords):
                budget_patterns = [
                    r'(?:under|below|less than|within|max|up to|budget of|around|spend)\s*₹?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(k|thousand|lakh)?',
                    r'₹\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(k|thousand|lakh)?',
                    r'(\d+)\s*(?:k|thousand)\s*(?:rupees|rs|inr)'
                ]
                for pat in budget_patterns:
                    b_match = re.search(pat, q_clean)
                    if b_match:
                        num_str = b_match.group(1).replace(',', '')
                        mult = b_match.group(2) if len(b_match.groups()) > 1 else None
                        try:
                            val = float(num_str)
                            if mult in ['k', 'thousand']:
                                val *= 1000.0
                            elif mult == 'lakh':
                                val *= 100000.0
                            req['max_price'] = val
                            break
                        except ValueError:
                            pass

        # 4. Detect Rating & Sort Preferences
        if any(term in q_clean for term in ['highly rated', 'high rating', 'top rated', 'best rating', 'good reviews', 'best reviews', '4+ star', '4+ stars']):
            req['min_rating'] = 4.0
            req['sort_preference'] = 'rating'
            req['quality_preference'] = 'top_rated'
        else:
            star_match = re.search(r'(?:rating\s*(?:above|over|>|>=)?\s*|above\s*|over\s*|)(\d(?:\.\d)?)\s*(?:star|\+?\s*rating|\+?\s*stars)', q_clean)
            if star_match:
                try:
                    r_val = float(star_match.group(1))
                    if 0.0 <= r_val <= 5.0:
                        req['min_rating'] = r_val
                        req['sort_preference'] = 'rating'
                except ValueError:
                    pass

        if any(term in q_clean for term in ['cheap', 'cheapest', 'affordable', 'budget', 'low price', 'lowest price', 'lowest cost', 'least expensive']):
            req['quality_preference'] = 'affordable'
            req['sort_preference'] = 'price_asc'
        elif any(term in q_clean for term in ['premium', 'expensive', 'flagship', 'high end', 'highest price', 'most expensive', 'highest cost']):
            req['quality_preference'] = 'premium'
            req['sort_preference'] = 'price_desc'

        # 5. Product Category & Intent Classification via Taxonomy
        matched_tax = []
        for tax_key, tax_info in cls.CATEGORY_TAXONOMY.items():
            for p_term in tax_info['primary_terms']:
                if re.search(r'\b' + re.escape(p_term) + r'\b', q_clean):
                    matched_tax.append((tax_key, tax_info))
                    break

        if matched_tax:
            best_key, best_info = matched_tax[0]
            req['product_intent'] = best_key
            req['product_type'] = best_key
            req['category_family'] = best_info.get('family', 'general')
            for cid in best_info['cat_ids']:
                if cid not in req['category_ids']:
                    req['category_ids'].append(cid)

        # 6. Use-case mapping & scenarios
        if 'programming' in q_clean or 'coding' in q_clean or 'developer' in q_clean:
            req['use_case'] = 'programming'
            req['attributes'].append('coding')
            if not req['product_intent'] and not req['is_accessory_request']:
                req['product_intent'] = 'laptop'
                req['product_type'] = 'laptop'
                req['category_family'] = 'electronics'
                req['category_ids'] = [1, 20]

        elif 'photography' in q_clean or 'photo' in q_clean or 'camera' in q_clean or 'vlog' in q_clean:
            req['use_case'] = 'photography'
            req['attributes'].append('photography')
            if not req['product_intent'] and not req['is_accessory_request']:
                req['product_intent'] = 'camera'
                req['product_type'] = 'camera'
                req['category_family'] = 'electronics'
                req['category_ids'] = [15]

        elif 'running' in q_clean or 'runner' in q_clean or 'jogging' in q_clean or 'marathon' in q_clean:
            req['use_case'] = 'running'
            req['attributes'].append('running')
            if not req['product_intent'] and not req['is_accessory_request']:
                req['product_intent'] = 'shoe'
                req['product_type'] = 'shoe'
                req['category_family'] = 'fashion'
                req['category_ids'] = [5, 35]

        elif 'cooking' in q_clean or 'cook' in q_clean or 'kitchen' in q_clean:
            req['use_case'] = 'cooking'
            if not req['product_intent'] and not req['is_accessory_request']:
                req['product_intent'] = 'kitchen_appliance'
                req['product_type'] = 'appliances'
                req['category_family'] = 'kitchen'
                req['category_ids'] = [10, 9]

        elif 'gift' in q_clean or 'present' in q_clean or 'sister' in q_clean or 'mother' in q_clean or 'friend' in q_clean or 'birthday' in q_clean:
            req['use_case'] = 'gift'
            req['category_family'] = 'gift'
            if not req['category_ids']:
                req['category_ids'] = [5, 6, 9, 27, 4, 3, 38]

        elif 'college' in q_clean or 'student' in q_clean or 'school' in q_clean or 'study' in q_clean:
            req['use_case'] = 'college'
            req['category_family'] = 'college'
            if not req['category_ids']:
                req['category_ids'] = [1, 20, 3, 31, 5]

        elif 'gaming' in q_clean or 'gamer' in q_clean:
            req['use_case'] = 'gaming'
            req['category_family'] = 'gaming'
            if not req['product_intent'] and not req['is_accessory_request']:
                req['product_intent'] = 'video_games'
                req['product_type'] = 'video_games'
                req['category_ids'] = [39, 20, 7]

        # 7. Dynamic Catalog Category Lookup via Token Overlap if not matched by taxonomy
        if not req['category_ids']:
            try:
                from app.models.category import Category
                active_db_cats = Category.query.filter_by(is_active=True).all()
                q_words = set(re.findall(r'\b[a-z0-9]+\b', q_clean))
                for db_cat in active_db_cats:
                    c_name_clean = db_cat.name.lower()
                    c_words = set(re.findall(r'\b[a-z0-9]+\b', c_name_clean)) - {'and', 'all', 'for', 'the', 'of', 'in', 'amazon'}
                    if c_words and (c_words.issubset(q_words) or (len(c_words) == 1 and bool(c_words & q_words))):
                        req['category_ids'].append(db_cat.id)
                        if not req['product_intent']:
                            req['product_intent'] = db_cat.slug.split('-')[0]
                            req['product_type'] = db_cat.slug.split('-')[0]
                            req['category_family'] = db_cat.slug.split('-')[0]
            except Exception:
                pass

        # 8. Multi-turn Follow-up Handling
        followup_phrases = ['which one', 'which is best', 'show cheaper ones', 'more expensive', 'in black', 'show more options', 'what about under']
        if conversation_history and any(fp in q_clean for fp in followup_phrases):
            for past in reversed(conversation_history):
                past_q = past.get('user_message', '')
                if past_q:
                    past_req = cls.extract_requirements(past_q)
                    if past_req.get('product_intent') and not req['product_intent']:
                        req['product_intent'] = past_req['product_intent']
                        req['product_type'] = past_req['product_type']
                        req['category_family'] = past_req['category_family']
                        req['category_ids'] = past_req['category_ids']
                        req['is_followup'] = True
                        if past_req.get('max_price') is not None and req['max_price'] is None:
                            req['max_price'] = past_req['max_price']
                        break

        # 9. Brand Matching
        brands = cls.get_cached_brands()
        for b_name in brands:
            if b_name and len(b_name) >= 2:
                if re.search(r'\b' + re.escape(b_name.lower()) + r'\b', q_clean):
                    req['brand'] = b_name
                    break

        return req

    @staticmethod
    def _parse_number(val_str):
        val_str = str(val_str).lower().strip().replace('₹', '').replace(',', '')
        if val_str.endswith('k'):
            try:
                return float(val_str[:-1]) * 1000.0
            except ValueError:
                return None
        try:
            return float(val_str)
        except ValueError:
            return None
