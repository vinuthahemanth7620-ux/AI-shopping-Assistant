import os
import re
import json
import logging
import google.generativeai as genai
from flask import current_app, session
from sqlalchemy import or_, and_, func, case
from app import db
from app.models.product import Product
from app.models.category import Category

logger = logging.getLogger(__name__)

USD_TO_INR = 83.0


class AIService:
    """
    AI Service Layer - Advanced Natural Language Understanding, Multi-Tier MySQL Product Retrieval Engine,
    Strict Relevance Validation & Disqualification Gate, Gemini API Integration, and Conversational Response Generation.
    Follows MVP Architecture.
    """

    # -------------------------------------------------------------------------
    # 1. CATEGORY TAXONOMY & STRICT RELEVANCE DEFINITIONS
    # -------------------------------------------------------------------------
    CATEGORY_TAXONOMY = {
        'laptop': {
            'cat_ids': [1, 20],
            'primary_terms': ['laptop', 'laptops', 'notebook', 'notebooks', 'macbook', 'chromebook', 'ultrabook', 'thinkpad', 'ideapad', 'pavilion', 'aspire', 'legion', 'zenbook', 'vivobook', 'inspiron', 'latitude', 'convertible', 'xps', 'zephyrus', 'surface pro'],
            'disqualifying_accessories': ['charger', 'adapter', 'power cord', 'power cable', 'mouse pad', 'mousepad', 'mouse', 'mice', 'keyboard', 'mat', 'desk pad', 'laptop bag', 'laptop backpack', 'laptop sleeve', 'laptop case', 'laptop skin', 'laptop stand', 'laptop holder', 'laptop charger', 'power adapter', 'laptop cable', 'screen protector', 'keyboard cover', 'docking station', 'usb hub', 'cooling pad', 'ram compatible', 'memory module for', 'memory upgrade for', 'screen replacement', 'battery replacement', 'decal sticker', 'mount holder', 'case cover', 'hard case', 'protective case']
        },
        'mobile': {
            'cat_ids': [2, 17],
            'primary_terms': ['phone', 'phones', 'mobile', 'mobiles', 'smartphone', 'smartphones', 'cellphone', 'cellphones', 'iphone', 'galaxy', 'pixel', 'redmi', 'oneplus', 'android'],
            'disqualifying_accessories': ['phone case', 'phone cover', 'screen protector', 'tempered glass', 'phone charger', 'charging cable', 'phone holder', 'car mount', 'phone mount', 'lanyard', 'replacement battery', 'repair kit', 'stylus pen', 'phone skin', 'wallet case', 'holster', 'ring holder', 'selfie stick', 'adapter converter', 'camera bracket', 'smart watch', 'smartwatch']
        },
        'headphone': {
            'cat_ids': [3, 28, 33, 17],
            'primary_terms': ['headphone', 'headphones', 'earphone', 'earphones', 'earbud', 'earbuds', 'headset', 'headsets', 'airpods', 'aonic', 'soundcore', 'bose quietcomfort', 'sennheiser hd'],
            'disqualifying_accessories': ['headphone case', 'headphone cover', 'headphone stand', 'headphone holder', 'headphone hanger', 'eartips', 'ear pads', 'headphone cushion', 'headphone cable', 'audio adapter', 'headphone amp', 'headphone amplifier', 'dust plug', 'cleaner kit']
        },
        'watch': {
            'cat_ids': [4, 5, 7],
            'primary_terms': ['watch', 'watches', 'smartwatch', 'smartwatches', 'fitbit', 'timepiece', 'chronograph'],
            'disqualifying_accessories': ['watch band', 'watch strap', 'watchband', 'watch bezel', 'screen protector', 'watch charger', 'charging cable', 'watch case', 'watch stand', 'watch winder', 'candle', 'lamp']
        },
        'shoe': {
            'cat_ids': [5, 35],
            'primary_terms': ['shoe', 'shoes', 'sneaker', 'sneakers', 'footwear', 'running shoe', 'running shoes', 'athletic shoe', 'athletic shoes', 'jogging shoe', 'walking shoe'],
            'disqualifying_accessories': ['necklace', 'pendant', 'ring', 'earrings', 'jewelry', 't-shirt', 'shirt', 'pants', 'socks', 'shoelace', 'insole', 'shoe horn', 'shoe tree', 'shoe polish', 'cleaner', 'shoe bag', 'towel', 'keychain', 'charm', 'cosplay costume', 'sandal', 'sandals', 'slipper', 'slippers', 'pump', 'heels', 'high heel', 'boot', 'boots', 'ankle boot']
        },
        'appliance': {
            'cat_ids': [10, 9],
            'primary_terms': ['mixer', 'blender', 'oven', 'microwave', 'air fryer', 'fryer', 'cooker', 'refrigerator', 'fridge', 'toaster', 'kettle', 'cookware', 'pot', 'pan', 'juicer', 'coffee maker', 'espresso machine', 'food processor', 'dishwasher', 'slow cooker', 'pressure cooker', 'waffle maker'],
            'disqualifying_accessories': ['cord organizer', 'cord wrap', 'cord holder', 'dust cover', 'appliance cover', 'magnet', 'dishwasher magnet', 'pull handle', 'finger pull', 'hinge', 'caulking', 'candle', 'night light', 'screw', 'faucet', 'rinser', 'glass rinser', 'mat', 'desk pad', 'push pins', 'light bulb', 'bulb', 'chandelier', 'pendant light']
        },
        'camera': {
            'cat_ids': [15],
            'primary_terms': ['camera', 'cameras', 'dslr', 'camcorder', 'action camera', 'dash cam', 'mirrorless camera', 'digital camera', 'vlogging camera'],
            'disqualifying_accessories': ['backdrop', 'background', 'camera bag', 'camera case', 'camera strap', 'tripod', 'monopod', 'camera lens', 'lens filter', 'cleaning kit', 'camera battery', 'camera charger', 'sd card', 'memory card', 'camera mount', 'camera bracket', 'cage', 'ring light', 'softbox', 'screen protector', 'security camera nvr']
        },
        'gaming': {
            'cat_ids': [39, 20, 7],
            'primary_terms': ['gaming', 'game', 'gamer', 'playstation', 'xbox', 'nintendo', 'console', 'controller', 'gamepad', 'rtx', 'gpu', 'gaming laptop', 'gaming desktop', 'gaming monitor', 'gaming headset', 'gaming mouse'],
            'disqualifying_accessories': ['door lock', 'caulking', 'cylinder']
        }
    }

    # Explicit Accessory Mapping (used when user asks explicitly for an accessory)
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

    _BRANDS_CACHE = None

    @classmethod
    def get_cached_brands(cls):
        """Cache active product brands in memory for instant matching."""
        if cls._BRANDS_CACHE is None:
            try:
                b_rows = db.session.query(Product.brand).filter(Product.is_active == True).distinct().all()
                cls._BRANDS_CACHE = [b[0] for b in b_rows if b[0] and len(b[0]) >= 2]
            except Exception as e:
                logger.error(f"Error caching brands: {str(e)}")
                return []
        return cls._BRANDS_CACHE

    @staticmethod
    def get_api_key():
        """Retrieve Gemini API key safely from Flask config or environment variables."""
        try:
            key = current_app.config.get('GEMINI_API_KEY') if current_app else os.getenv('GEMINI_API_KEY')
            return key.strip() if key else ''
        except Exception as e:
            logger.error(f"Error fetching GEMINI_API_KEY: {str(e)}")
            return ''

    # -------------------------------------------------------------------------
    # 2. NATURAL LANGUAGE INTENT EXTRACTION & MULTI-TURN CONTEXT
    # -------------------------------------------------------------------------
    @classmethod
    def extract_user_intent(cls, user_query, conversation_history=None):
        """
        Extract structured shopping intent from user query:
        - product_type: Primary item concept ('laptop', 'mobile', 'headphone', 'camera', 'shoe', 'appliance', 'watch', etc.)
        - use_case: Targeted intent ('running', 'photography', 'programming', 'gaming', 'gift', 'college', 'travel', etc.)
        - is_primary_request: True if user asks for a core device/item
        - is_accessory_request: True ONLY if user explicitly requests an accessory
        - target_accessory: Requested accessory term ('mouse', 'bag', 'tripod', 'case', etc.)
        - category_ids: List of database Category IDs matching intent
        - max_price / min_price: Extracted numeric budget limits (in INR)
        - min_rating: Min rating preference
        - sort_preference: 'recommended', 'rating', 'price_asc', 'price_desc'
        - is_followup: True if current query relies on multi-turn context
        """
        query_text = user_query.strip().lower()

        intent = {
            'product_type': None,
            'use_case': None,
            'category_ids': [],
            'category_names': [],
            'max_price': None,
            'min_price': None,
            'brand': None,
            'min_rating': None,
            'sort_preference': 'recommended',
            'search_terms': [],
            'query_type': 'general',
            'is_primary_request': True,
            'is_accessory_request': False,
            'target_accessory': None,
            'is_followup': False,
            'original_query': user_query
        }

        # Step A: Parse Stop Words & Search Terms
        stop_words = {
            'i', 'need', 'show', 'me', 'find', 'suggest', 'give', 'a', 'an', 'the', 'for', 'with',
            'under', 'below', 'less', 'than', 'between', 'and', 'my', 'best', 'good', 'top', 'rated',
            'highly', 'which', 'what', 'product', 'products', 'something', 'one', 'items', 'item',
            'recommend', 'looking', 'want', 'please', 'can', 'you', 'have', 'do', 'in', 'of', 'on', 'at', 'buy'
        }
        words = [w for w in re.findall(r'\b[a-z0-9]+\b', query_text) if len(w) >= 2]
        intent['search_terms'] = [w for w in words if w not in stop_words]

        # Step B: EXPLICIT ACCESSORY INTENT DETECTION
        accessory_triggers = {
            'mouse': [r'\bmouse\b', r'\bmice\b', r'\bmouse for\b'],
            'bag': [r'\blaptop bag\b', r'\blaptop backpack\b', r'\blaptop sleeve\b', r'\bbag for laptop\b'],
            'tripod': [r'\btripod\b', r'\bmonopod\b', r'\bcamera tripod\b'],
            'case': [r'\bphone case\b', r'\bphone cover\b', r'\bcase for phone\b', r'\bcover for phone\b']
        }

        for acc_type, patterns in accessory_triggers.items():
            if any(re.search(pat, query_text) for pat in patterns):
                intent['is_accessory_request'] = True
                intent['is_primary_request'] = False
                intent['target_accessory'] = acc_type
                break

        # Step C: Detect Price / Budget Constraints
        range_match = re.search(r'between\s*₹?\s*(\d+k?)\s*and\s*₹?\s*(\d+k?)', query_text)
        if range_match:
            min_v = cls._parse_number_str(range_match.group(1))
            max_v = cls._parse_number_str(range_match.group(2))
            if min_v and max_v:
                intent['min_price'] = min_v
                intent['max_price'] = max_v
                intent['query_type'] = 'budget'

        if intent['max_price'] is None:
            budget_patterns = [
                r'(?:under|below|less than|within|max|up to|budget of|around|spend)\s*₹?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(k|thousand|lakh)?',
                r'₹\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(k|thousand|lakh)?',
                r'(\d+)\s*(?:k|thousand)\s*(?:rupees|rs|inr)?'
            ]
            for pattern in budget_patterns:
                b_match = re.search(pattern, query_text)
                if b_match:
                    raw_num = b_match.group(1).replace(',', '')
                    multiplier = b_match.group(2) if len(b_match.groups()) > 1 else None
                    try:
                        val = float(raw_num)
                        if multiplier in ['k', 'thousand']:
                            val *= 1000
                        elif multiplier == 'lakh':
                            val *= 100000
                        intent['max_price'] = val
                        intent['query_type'] = 'budget'
                        break
                    except ValueError:
                        pass

        # Step D: Detect Rating & Sort Preferences
        rating_terms = ['best rated', 'highest rating', 'top rated', 'high rating', 'most rated', 'good reviews', 'best review', 'highest ratings', 'best ratings']
        if any(term in query_text for term in rating_terms):
            intent['min_rating'] = 4.0
            intent['sort_preference'] = 'rating'
            intent['query_type'] = 'rating'
        else:
            star_match = re.search(r'(\d(?:\.\d)?)\s*(?:star|\+?\s*rating)', query_text)
            if star_match:
                try:
                    r_val = float(star_match.group(1))
                    if 0.0 <= r_val <= 5.0:
                        intent['min_rating'] = r_val
                        intent['sort_preference'] = 'rating'
                except ValueError:
                    pass

        if any(term in query_text for term in ['cheapest', 'affordable', 'budget friendly', 'low price', 'lowest price', 'lowest cost', 'least expensive']):
            intent['sort_preference'] = 'price_asc'
        elif any(term in query_text for term in ['premium', 'expensive', 'high end', 'flagship', 'highest price', 'most expensive']):
            intent['sort_preference'] = 'price_desc'

        # Step E: Match Query against Category Taxonomy Map
        matched_taxonomies = []
        for key, tax_info in cls.CATEGORY_TAXONOMY.items():
            for p_term in tax_info['primary_terms']:
                if re.search(r'\b' + re.escape(p_term) + r'\b', query_text):
                    matched_taxonomies.append(key)
                    for cid in tax_info['cat_ids']:
                        if cid not in intent['category_ids']:
                            intent['category_ids'].append(cid)
                    break

        if matched_taxonomies:
            intent['product_type'] = matched_taxonomies[0]

        # Step F: Detect Use Cases & Scenarios
        if 'running' in query_text or 'runner' in query_text or 'jogging' in query_text:
            intent['use_case'] = 'running'
            if not intent['product_type'] and not intent['is_accessory_request']:
                intent['product_type'] = 'shoe'
                intent['category_ids'] = [5, 35]

        elif 'cooking' in query_text or 'cook' in query_text or 'kitchen' in query_text:
            intent['use_case'] = 'cooking'
            if not intent['product_type'] and not intent['is_accessory_request']:
                intent['product_type'] = 'appliance'
                intent['category_ids'] = [10, 9]

        elif 'photography' in query_text or 'photo' in query_text or 'photos' in query_text or 'camera' in query_text:
            intent['use_case'] = 'photography'
            if not intent['product_type'] and not intent['is_accessory_request']:
                intent['product_type'] = 'camera'
                intent['category_ids'] = [15]

        elif 'programming' in query_text or 'coding' in query_text or 'developer' in query_text:
            intent['use_case'] = 'programming'
            if not intent['product_type'] and not intent['is_accessory_request']:
                intent['product_type'] = 'laptop'
                intent['category_ids'] = [1, 20]

        elif 'gaming' in query_text or 'game' in query_text or 'gamer' in query_text:
            intent['use_case'] = 'gaming'
            if not intent['product_type'] and not intent['is_accessory_request']:
                intent['product_type'] = 'gaming'
                intent['category_ids'] = [39, 20, 7]

        elif 'gift' in query_text or 'present' in query_text or 'mother' in query_text or 'mom' in query_text or 'sister' in query_text:
            intent['use_case'] = 'gift'
            intent['category_ids'] = [5, 6, 9, 27, 4, 3]

        elif 'college' in query_text or 'student' in query_text or 'school' in query_text or 'study' in query_text:
            intent['use_case'] = 'college'
            intent['category_ids'] = [1, 20, 3, 31, 5]

        elif 'travel' in query_text or 'travelling' in query_text or 'trip' in query_text or 'vacation' in query_text:
            intent['use_case'] = 'travel'
            intent['category_ids'] = [5, 3, 15, 35]

        # Step G: MULTI-TURN CONVERSATIONAL CONTEXT PRESERVATION
        followup_phrases = ['which one', 'which is best', 'cheaper', 'expensive', 'for programming', 'for gaming', 'for photography', 'under']
        is_short = len(query_text.split()) <= 5

        if (any(ph in query_text for ph in followup_phrases) or is_short) and conversation_history:
            for past in reversed(conversation_history):
                past_q = past.get('user_message', '').strip()
                if past_q:
                    past_intent = cls._quick_parse_intent(past_q)
                    if past_intent.get('product_type'):
                        if not intent['product_type']:
                            intent['product_type'] = past_intent['product_type']
                            intent['category_ids'] = past_intent.get('category_ids', intent['category_ids'])
                            intent['is_followup'] = True
                        if past_intent.get('max_price') is not None and intent['max_price'] is None:
                            intent['max_price'] = past_intent['max_price']
                        break

        # Step H: Brand Matching
        brands = cls.get_cached_brands()
        for b_name in brands:
            if b_name and len(b_name) >= 2:
                if re.search(r'\b' + re.escape(b_name.lower()) + r'\b', query_text):
                    intent['brand'] = b_name
                    break

        return intent

    # -------------------------------------------------------------------------
    # 3. STRICT RELEVANCE VALIDATION GATE (Rejection Log & Negative Rules)
    # -------------------------------------------------------------------------
    @classmethod
    def validate_product_relevance(cls, product, intent):
        """
        Strict validation filter to enforce positive & negative product relevance AND hard budget limits.
        Returns (is_valid, rejection_reason).
        """
        if not product:
            return False, "NULL_PRODUCT"

        norm_price = float(product.normalized_price_inr)
        p_name_lower = product.name.lower()
        cat_id = product.category_id
        p_type = intent.get('product_type')
        is_acc_req = intent.get('is_accessory_request', False)
        is_prim_req = intent.get('is_primary_request', True)
        target_acc = intent.get('target_accessory')

        # 1. HARD BUDGET LIMIT ENFORCEMENT
        if intent.get('max_price') is not None:
            if norm_price > float(intent['max_price']):
                return False, f"BUDGET_EXCEEDED (Price ₹{norm_price:,.2f} > Max ₹{intent['max_price']:,.2f})"

        if intent.get('min_price') is not None:
            if norm_price < float(intent['min_price']):
                return False, f"MIN_PRICE_UNMET (Price ₹{norm_price:,.2f} < Min ₹{intent['min_price']:,.2f})"

        # 2. EXPLICIT ACCESSORY REQUEST VALIDATION
        if is_acc_req and target_acc:
            if 'bag' in target_acc or 'sleeve' in target_acc or 'backpack' in target_acc:
                if not (('laptop' in p_name_lower or 'computer' in p_name_lower or 'macbook' in p_name_lower or 'notebook' in p_name_lower) and
                        ('bag' in p_name_lower or 'backpack' in p_name_lower or 'sleeve' in p_name_lower or 'case' in p_name_lower or 'tote' in p_name_lower)):
                    return False, "ACCESSORY_MISMATCH (Not a laptop bag/sleeve)"

            elif 'tripod' in target_acc or 'monopod' in target_acc:
                if not ('tripod' in p_name_lower or 'monopod' in p_name_lower):
                    return False, "ACCESSORY_MISMATCH (Not a camera tripod/monopod)"
                if any(bad in p_name_lower for bad in ['digital camera', 'dslr camera', 'camcorder']):
                    return False, "ACCESSORY_MISMATCH (Full camera returned for tripod request)"

            elif 'case' in target_acc or 'cover' in target_acc:
                if not (('phone' in p_name_lower or 'iphone' in p_name_lower or 'galaxy' in p_name_lower or 'pixel' in p_name_lower or 'cell' in p_name_lower or 'airpods' in p_name_lower or 'headphone' in p_name_lower or 'earbud' in p_name_lower) and
                        ('case' in p_name_lower or 'cover' in p_name_lower)):
                    return False, "ACCESSORY_MISMATCH (Not a case/cover)"

            elif 'mouse' in target_acc:
                if not ('mouse' in p_name_lower or 'mice' in p_name_lower):
                    return False, "ACCESSORY_MISMATCH (Not a computer mouse)"
                if 'mouse pad' in p_name_lower or 'mousepad' in p_name_lower:
                    return False, "ACCESSORY_MISMATCH (Mouse pad rejected for mouse request)"

            return True, "VALID_ACCESSORY"

        # 3. PRIMARY DEVICE/ITEM REQUEST VALIDATION & NOISE PURGING
        if is_prim_req and p_type and p_type in cls.CATEGORY_TAXONOMY:
            tax_info = cls.CATEGORY_TAXONOMY[p_type]
            primary_terms = tax_info['primary_terms']
            disqualifying_accessories = tax_info['disqualifying_accessories']

            # Check disqualifying accessory phrases in product title
            for dis_acc in disqualifying_accessories:
                if re.search(r'\b' + re.escape(dis_acc) + r'\b', p_name_lower):
                    return False, f"ACCESSORY_MISMATCH (Primary request for '{p_type}', rejected accessory phrase '{dis_acc}')"

            # Primary Title Strictness Check
            has_primary_title = any(re.search(r'\b' + re.escape(pt) + r'\b', p_name_lower) for pt in primary_terms)

            # Category restriction check
            allowed_cats = tax_info.get('cat_ids', [])
            if allowed_cats and cat_id not in allowed_cats and not has_primary_title:
                return False, f"WRONG_CATEGORY (Category ID {cat_id} not in allowed {allowed_cats})"

            if not has_primary_title:
                return False, f"PRODUCT_TYPE_MISMATCH (Title lacks required primary terms for '{p_type}')"

        # 4. SPECIFIC USE-CASE PRODUCT SANITY CHECKS & STRICT PRIMARY ACCESSORY PURGING
        if is_prim_req:
            if p_type == 'mobile':
                if any(bad in p_name_lower for bad in ['case', 'cover', 'protector', 'tempered glass', 'charger', 'cable', 'mount', 'lanyard', 'holster', 'armband', 'ring holder', 'selfie stick', 'skin', 'replacement battery', 'stylus']):
                    return False, "ACCESSORY_MISMATCH (Phone accessory rejected for primary phone request)"

            elif p_type == 'headphone':
                if any(bad in p_name_lower for bad in ['case', 'cover', 'stand', 'holder', 'hanger', 'eartips', 'ear pad', 'cushion', 'cable', 'adapter', 'amp', 'amplifier', 'plug', 'cleaner', 'pouch', 'carrying organizer']):
                    return False, "ACCESSORY_MISMATCH (Headphone accessory rejected for primary headphone request)"

            elif p_type == 'camera':
                if any(bad in p_name_lower for bad in ['backdrop', 'background', 'bag', 'case', 'strap', 'tripod', 'monopod', 'lens', 'filter', 'sd card', 'memory card', 'mount', 'bracket', 'cage', 'nvr', 'level', 'screw', 'cap', 'cover', 'holder', 'rubber', 'mask', 'housing', 'plate', 'cable', 'charger', 'battery', 'adapter']):
                    return False, "ACCESSORY_MISMATCH (Camera accessory rejected for primary camera request)"

            elif p_type == 'watch':
                if any(bad in p_name_lower for bad in ['band', 'strap', 'watchband', 'bezel', 'screen protector', 'charger', 'cable', 'case', 'stand', 'winder', 'candle', 'lamp']):
                    return False, "ACCESSORY_MISMATCH (Watch accessory rejected for primary watch request)"

            elif p_type == 'appliance':
                if any(bad in p_name_lower for bad in ['light', 'bulb', 'handle', 'pull', 'hinge', 'candle', 'wrap', 'organizer', 'magnet', 'cover', 'replacement filter', 'filter', 'mat', 'pad', 'cord']):
                    return False, "ACCESSORY_MISMATCH (Appliance accessory rejected for primary appliance request)"

        if intent.get('use_case') == 'running' or p_type == 'shoe':
            running_shoe_terms = ['shoe', 'shoes', 'sneaker', 'sneakers', 'footwear', 'running shoe', 'running shoes', 'athletic shoe', 'athletic shoes', 'jogging shoe', 'walking shoe']
            if not any(st in p_name_lower for st in running_shoe_terms):
                return False, "PRODUCT_TYPE_MISMATCH (Not a shoe/footwear)"
            if any(bad in p_name_lower for bad in ['necklace', 'pendant', 'ring', 'earrings', 'jewelry', 't-shirt', 'socks', 'lace', 'insole', 'sandal', 'sandals', 'slipper', 'slippers', 'pump', 'heels', 'high heel', 'boot', 'boots', 'ankle boot', 'cosplay']):
                return False, "CROSS_CATEGORY_NOISE (Rejected non-running shoe fashion item)"

        if intent.get('use_case') == 'cooking' or p_type == 'appliance':
            kitchen_kws = ['mixer', 'blender', 'oven', 'microwave', 'fryer', 'cooker', 'refrigerator', 'fridge', 'toaster', 'kettle', 'cookware', 'pot', 'pan', 'juicer', 'coffee', 'espresso', 'processor', 'dishwasher', 'waffle maker']
            if cat_id == 10:  # Appliances category
                if any(bad in p_name_lower for bad in ['light', 'bulb', 'handle', 'pull', 'hinge', 'candle', 'cord wrap', 'cord organizer', 'magnet', 'cover']):
                    return False, "ACCESSORY_MISMATCH (Appliance accessory rejected)"
            else:
                if not any(kk in p_name_lower for kk in kitchen_kws):
                    return False, "PRODUCT_TYPE_MISMATCH (Not a kitchen appliance)"

        if intent.get('use_case') == 'photography' or p_type == 'camera':
            if not any(ck in p_name_lower for ck in ['camera', 'dslr', 'camcorder', 'action camera', 'dash cam', 'digital camera', 'vlogging camera', 'mirrorless camera']):
                return False, "PRODUCT_TYPE_MISMATCH (Not a camera device)"
            if any(bad in p_name_lower for bad in ['backdrop', 'background', 'bag', 'case', 'strap', 'tripod', 'monopod', 'lens', 'filter', 'sd card', 'cage', 'nvr', 'mount', 'holder', 'cap', 'cover', 'rubber', 'mask', 'housing', 'plate', 'bracket', 'cable', 'charger', 'battery', 'adapter']):
                return False, "ACCESSORY_MISMATCH (Camera accessory rejected)"

        if intent.get('use_case') == 'programming' or p_type == 'laptop':
            if not any(lk in p_name_lower for lk in ['laptop', 'notebook', 'macbook', 'chromebook', 'ultrabook', 'aspire', 'ideapad', 'thinkpad', 'pavilion', 'legion', 'zenbook', 'vivobook', 'inspiron', 'latitude', 'convertible', 'xps', 'zephyrus', 'surface pro']):
                return False, "PRODUCT_TYPE_MISMATCH (Not a laptop computer)"
            if any(bad in p_name_lower for bad in ['laptop bag', 'laptop backpack', 'laptop sleeve', 'laptop case', 'laptop skin', 'laptop stand', 'laptop charger', 'keyboard cover', 'docking station', 'cooling pad', 'ram compatible', 'charger', 'adapter', 'power cord', 'power cable', 'screen protector', 'decal', 'sticker', 'mount', 'mouse pad', 'mousepad', 'mouse', 'mice', 'keyboard', 'mat', 'replacement battery', 'memory module']):
                return False, "ACCESSORY_MISMATCH (Laptop accessory rejected)"

        if p_type == 'watch':
            if not any(wk in p_name_lower for wk in ['watch', 'watches', 'smartwatch', 'smartwatches', 'fitbit', 'timepiece', 'chronograph']):
                return False, "PRODUCT_TYPE_MISMATCH (Not a wristwatch)"
            if any(bad in p_name_lower for bad in ['watch band', 'watch strap', 'watchband', 'bezel', 'screen protector', 'watch charger', 'watch case', 'candle']):
                return False, "ACCESSORY_MISMATCH (Watch accessory rejected)"

        # Purge hardware tools from open-ended gift/college/travel queries
        if intent.get('use_case') in ['gift', 'college', 'travel', 'gaming']:
            if any(bad in p_name_lower for bad in ['door lock', 'cylinder lock', 'caulking', 'chemical', 'gasket', 'nozzle tool']):
                return False, "CROSS_CATEGORY_NOISE (Irrelevant hardware tool rejected)"

        return True, "VALID"

    # -------------------------------------------------------------------------
    # 4. MULTI-TIER MYSQL PRODUCT RETRIEVAL ENGINE
    # -------------------------------------------------------------------------
    @classmethod
    def retrieve_relevant_products(cls, intent, user_query, limit=8):
        """
        Execute SQL search across actual MySQL product catalog:
        1. Dual-Currency Price Expression Filter.
        2. Category ID filtering.
        3. Title-first ILIKE keyword matching.
        4. Composite Score Ranking.
        5. Validation Gate with Rejection Logs.
        """
        norm_price_expr = case(
            (and_(Product.category_id > 4, Product.price < 3000.0), Product.price * USD_TO_INR),
            else_=Product.price
        )

        base_query = Product.query.filter(Product.is_active == True, Product.is_available == True)

        # Apply Price Filters
        max_p = intent.get('max_price')
        min_p = intent.get('min_price')
        if max_p is not None:
            base_query = base_query.filter(norm_price_expr <= float(max_p))
        if min_p is not None:
            base_query = base_query.filter(norm_price_expr >= float(min_p))

        # Apply Rating Filter
        if intent.get('min_rating') is not None:
            base_query = base_query.filter(Product.rating >= intent['min_rating'])

        # Apply Brand Filter
        if intent.get('brand'):
            base_query = base_query.filter(Product.brand.ilike(f"%{intent['brand']}%"))

        candidates = []
        cat_ids = intent.get('category_ids', [])
        search_terms = intent.get('search_terms', [])
        p_type = intent.get('product_type')
        is_acc = intent.get('is_accessory_request', False)
        target_acc = intent.get('target_accessory')

        # Target Title Terms Resolution
        title_terms = list(search_terms)
        if p_type and p_type in cls.CATEGORY_TAXONOMY:
            title_terms.extend(cls.CATEGORY_TAXONOMY[p_type]['primary_terms'][:6])

        if is_acc and target_acc in cls.ACCESSORY_ROUTING:
            acc_routing = cls.ACCESSORY_ROUTING[target_acc]
            title_terms = acc_routing['target_terms']
            cat_ids = acc_routing['cat_ids']

        title_clauses = [Product.name.ilike(f"%{term}%") for term in title_terms if len(term) >= 2]

        # TIER 1: Category ID & Title Terms Match
        if cat_ids and title_clauses:
            q_tier1 = base_query.filter(and_(Product.category_id.in_(cat_ids), or_(*title_clauses)))
            candidates = q_tier1.order_by(Product.rating.desc()).limit(80).all()

        # TIER 2: Title Terms Match across all categories
        if not candidates and title_clauses:
            q_tier2 = base_query.filter(or_(*title_clauses))
            candidates = q_tier2.order_by(Product.rating.desc()).limit(80).all()

        # TIER 3: Category ID match alone if open-ended
        if not candidates and cat_ids:
            q_tier3 = base_query.filter(Product.category_id.in_(cat_ids))
            candidates = q_tier3.order_by(Product.rating.desc()).limit(80).all()

        # TIER 4: Fallback Candidate List
        if not candidates:
            candidates = base_query.order_by(Product.rating.desc()).limit(80).all()

        # ---------------------------------------------------------
        # COMPOSITE RELEVANCE SCORING & REJECTION LOGGING
        # ---------------------------------------------------------
        validated_products = []
        rejected_log = []
        candidate_log = []

        for p in candidates:
            candidate_log.append(f"[ID {p.id}] {p.name[:50]}")
            is_valid, reason = cls.validate_product_relevance(p, intent)

            if not is_valid:
                rejected_log.append(f"[ID {p.id}] {p.name[:45]} -> REASON: {reason}")
                continue

            # Compute Composite Relevance Score (4 Tiers)
            score = float(p.rating or 0.0) * 100.0
            p_name_lower = p.name.lower()
            cat_id = p.category_id

            # Tier 1 (+2000 pts): Target Category & Title Match
            if cat_ids and cat_id in cat_ids:
                score += 2000.0

            # Tier 2 (+1000 pts): Primary Title Keyword Match
            if p_type and p_type in cls.CATEGORY_TAXONOMY:
                prim_kws = cls.CATEGORY_TAXONOMY[p_type]['primary_terms']
                if any(kw in p_name_lower for kw in prim_kws):
                    score += 1000.0

            # Tier 3 (+1500 pts): Explicit Accessory Title Match
            if is_acc and target_acc in cls.ACCESSORY_ROUTING:
                acc_terms = cls.ACCESSORY_ROUTING[target_acc]['target_terms']
                if any(at in p_name_lower for at in acc_terms):
                    score += 1500.0

            # Tier 4 (+300 pts): Brand match
            if intent.get('brand') and intent['brand'].lower() in p.brand.lower():
                score += 300.0

            validated_products.append((score, p))

        # Sorting Strategy
        if intent.get('sort_preference') == 'price_asc':
            validated_products.sort(key=lambda x: float(x[1].normalized_price_inr))
        elif intent.get('sort_preference') == 'price_desc':
            validated_products.sort(key=lambda x: float(x[1].normalized_price_inr), reverse=True)
        elif intent.get('sort_preference') == 'rating':
            validated_products.sort(key=lambda x: float(x[1].rating or 0.0), reverse=True)
        else:
            validated_products.sort(key=lambda x: x[0], reverse=True)

        final_products = [item[1] for item in validated_products[:limit]]

        # MANDATORY DETAILED DEBUG LOGGING FORMAT
        logger.info("=" * 60)
        logger.info(f"[AI QUERY] Original Query: {user_query}")
        logger.info(f"[AI INTENT] Product Type: {intent.get('product_type')} | Use Case: {intent.get('use_case')} | Max Price: {intent.get('max_price')} | Min Price: {intent.get('min_price')} | Rating Pref: {intent.get('min_rating')} | Is Accessory: {intent.get('is_accessory_request')} (Target: {intent.get('target_accessory')})")
        logger.info(f"[DATABASE SEARCH] Search Terms: {intent.get('search_terms')} | Target Categories: {intent.get('category_ids')} | Total Candidates: {len(candidates)}")
        logger.info(f"[CANDIDATE PRODUCTS] Candidates fetched from DB: {len(candidate_log)} items")
        logger.info(f"[RELEVANCE FILTER] Validated Products: {len(final_products)} | Total Rejected: {len(rejected_log)}")
        if rejected_log:
            logger.info(f"[REJECTED PRODUCTS]\n" + "\n".join(rejected_log[:15]))
        logger.info(f"[FINAL RESULTS] Returned {len(final_products)} products:")
        for idx, fp in enumerate(final_products, 1):
            cat_name = fp.category.name if fp.category else 'N/A'
            logger.info(f"   {idx}. [ID {fp.id}] {fp.name[:60]} | Cat: {cat_name} | Price: ₹{fp.normalized_price_inr:,.2f} | Rating: {fp.rating}")
        logger.info("=" * 60)

        # Print to console for real-time terminal output safely
        try:
            print(f"\n[AI QUERY] {user_query}")
            print(f"[AI INTENT] Product Type: {intent.get('product_type')}, Use Case: {intent.get('use_case')}, Max Price: {intent.get('max_price')}, Is Accessory: {intent.get('is_accessory_request')}")
            print(f"[DATABASE SEARCH] Candidates: {len(candidates)} -> Validated: {len(final_products)} (Rejected: {len(rejected_log)})")
        except Exception:
            pass

        return final_products

    # -------------------------------------------------------------------------
    # 5. SPECIALIZED DATASET EXECUTORS & HELPER METHODS
    # -------------------------------------------------------------------------
    @classmethod
    def _quick_parse_intent(cls, text):
        """Helper to parse intent from historical query string for multi-turn context."""
        return cls.extract_user_intent(text)

    @staticmethod
    def _parse_number_str(val_str):
        """Helper to parse numeric budget strings like '20k', '50000', '15'."""
        val_str = val_str.lower().strip().replace('₹', '').replace(',', '')
        if val_str.endswith('k'):
            try:
                return float(val_str[:-1]) * 1000
            except ValueError:
                return None
        try:
            return float(val_str)
        except ValueError:
            return None

    @classmethod
    def get_dataset_statistics(cls, query_text):
        """Query actual dataset statistics from MySQL database."""
        q_lower = query_text.lower()
        if any(term in q_lower for term in ['how many product', 'total product', 'items available', 'catalog size', 'products available']):
            total_p = db.session.query(func.count(Product.id)).filter(Product.is_active == True).scalar() or 0
            return f"Our catalog database currently contains **{total_p:,}** active products across 39 product categories."

        total_p = db.session.query(func.count(Product.id)).filter(Product.is_active == True).scalar() or 0
        total_c = db.session.query(func.count(Category.id)).filter(Category.is_active == True).scalar() or 0
        avg_r = db.session.query(func.avg(Product.rating)).filter(Product.is_active == True).scalar() or 0.0
        return (
            f"Here are key catalog dataset statistics from MySQL:\n"
            f"• **Total Products**: {total_p:,}\n"
            f"• **Total Categories**: {total_c}\n"
            f"• **Average Catalog Rating**: {float(avg_r):.2f} / 5.0★"
        )

    @classmethod
    def generate_product_comparison(cls, products):
        """
        Generate a side-by-side comparison table formatted string for a list of products.
        """
        if not products:
            return "No products available for comparison."

        headers = ["Attribute"] + [f"{p.name[:30]}..." for p in products]
        rows = [
            ["Price (INR)"] + [f"₹{p.normalized_price_inr:,.2f}" for p in products],
            ["Brand"] + [p.brand for p in products],
            ["Rating"] + [f"{float(p.rating):.1f}★" for p in products],
            ["Category"] + [(p.category.name if p.category else "General") for p in products]
        ]

        table_str = "| " + " | ".join(headers) + " |\n"
        table_str += "| " + " | ".join(["---"] * len(headers)) + " |\n"
        for r in rows:
            table_str += "| " + " | ".join(r) + " |\n"

        return table_str

    # -------------------------------------------------------------------------
    # 6. AI RESPONSE GENERATION & GEMINI INTEGRATION
    # -------------------------------------------------------------------------
    @classmethod
    def generate_ai_response(cls, user_query, user_id=None, conversation_history=None):
        """
        Main entry point for AI recommendations:
        1. Extract natural language intent (incorporating conversation history context)
        2. Query MySQL database for matching products via multi-tier retrieval engine
        3. Build structured catalog context
        4. Call Gemini API for response synthesis OR generate local natural response
        5. Return response dictionary
        """
        user_query_clean = user_query.strip()
        if not user_query_clean:
            return {
                'success': False,
                'ai_response': "Please ask a question about products or shopping.",
                'recommended_products': [],
                'intent': 'empty'
            }

        # Step 1: Extract intent
        intent = cls.extract_user_intent(user_query_clean, conversation_history=conversation_history)
        q_type = intent.get('query_type', 'general')

        # Dataset queries
        if q_type == 'dataset_query':
            return {
                'success': True,
                'ai_response': cls.get_dataset_statistics(user_query_clean),
                'recommended_products': [],
                'intent': q_type
            }

        # Step 2: Retrieve products from MySQL catalog
        products = cls.retrieve_relevant_products(intent, user_query_clean)

        api_key = cls.get_api_key()

        # Local natural AI response synthesis when Gemini API key is absent
        if not api_key:
            ai_text = cls._generate_local_natural_response(user_query_clean, intent, products)
            return {
                'success': True,
                'ai_response': ai_text,
                'recommended_products': products,
                'intent': q_type
            }

        # Gemini Prompt Formulation
        catalog_context = cls.build_structured_context(products)
        system_prompt = (
            "You are the 'AI Shopping Assistant' for an e-commerce platform.\n"
            "Your objective is to provide helpful, polite, and natural shopping recommendations.\n\n"
            "STRICT RULES:\n"
            "1. ONLY recommend products explicitly listed in the DATABASE CATALOG CONTEXT provided below.\n"
            "2. NEVER fabricate or invent product names, prices, specs, ratings, or availability.\n"
            "3. Format product recommendations cleanly with Bullet points, Name, Price (in ₹), Rating, and a brief explanation of why it fits their request.\n"
            "4. Be conversational, helpful, and clear.\n"
        )

        history_text = ""
        if conversation_history:
            history_text = "\nRECENT CONVERSATION HISTORY:\n"
            for item in conversation_history[-3:]:
                history_text += f"User: {item.get('user_message', '')}\nAI: {item.get('ai_response', '')}\n"

        prompt = (
            f"{system_prompt}\n"
            f"{history_text}\n"
            f"DATABASE CATALOG CONTEXT:\n"
            f"=======================\n"
            f"{catalog_context}\n"
            f"=======================\n\n"
            f"USER QUESTION: {user_query_clean}\n\n"
            f"ASSISTANT RESPONSE:"
        )

        try:
            genai.configure(api_key=api_key)
            model_names = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
            ai_text = None
            last_err = None

            for m_name in model_names:
                try:
                    model = genai.GenerativeModel(m_name)
                    response = model.generate_content(prompt)
                    if response and hasattr(response, 'text') and response.text:
                        ai_text = response.text.strip()
                        break
                except Exception as ex:
                    last_err = ex

            if not ai_text:
                ai_text = cls._generate_local_natural_response(user_query_clean, intent, products)

            return {
                'success': True,
                'ai_response': ai_text,
                'recommended_products': products,
                'intent': intent.get('query_type', 'general')
            }

        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}")
            ai_text = cls._generate_local_natural_response(user_query_clean, intent, products)
            return {
                'success': True,
                'ai_response': ai_text,
                'recommended_products': products,
                'intent': intent.get('query_type', 'general')
            }

    @staticmethod
    def build_structured_context(products):
        """Build clean text context from database products for Gemini prompt."""
        if not products:
            return "NO MATCHING PRODUCTS FOUND IN CATALOG DATABASE."

        catalog_entries = []
        for index, p in enumerate(products, 1):
            category_name = p.category.name if p.category else "General"
            specs = json.dumps(p.specifications) if isinstance(p.specifications, dict) else (p.specifications or "N/A")
            catalog_entries.append(
                f"{index}. Product ID: {p.id}\n"
                f"   Name: {p.name}\n"
                f"   Brand: {p.brand}\n"
                f"   Category: {category_name}\n"
                f"   Price: ₹{p.normalized_price_inr:,.2f}\n"
                f"   Rating: {float(p.rating):.1f} / 5.0\n"
                f"   In Stock: {'Yes (' + str(p.stock_quantity) + ' units)' if p.stock_quantity > 0 else 'No'}\n"
                f"   Description: {p.description or 'N/A'}\n"
                f"   Key Specifications: {specs}\n"
            )
        return "\n".join(catalog_entries)

    @classmethod
    def _generate_local_natural_response(cls, user_query, intent, products):
        """
        Generate natural language AI response locally when Gemini API key is absent.
        """
        if not products:
            p_type = intent.get('product_type') or "item"
            max_p = intent.get('max_price')
            if max_p:
                return f"I couldn't find a matching **{p_type}** under **₹{max_p:,.0f}** in our catalog database. Would you like to adjust your budget or search for top-rated alternatives?"
            return "I couldn't find a matching product in our catalog for your exact request. Try adjusting your query or budget!"

        intro = ""
        p_type = intent.get('product_type') or "products"
        use_c = intent.get('use_case')
        max_p = intent.get('max_price')
        is_acc = intent.get('is_accessory_request')
        target_acc = intent.get('target_accessory')

        if is_acc and target_acc:
            intro = f"Here are relevant **{target_acc}** options for your request from our catalog:"
        elif use_c and max_p:
            intro = f"Here are great options for **{use_c.replace('_', ' ')}** under **₹{max_p:,.0f}** from our catalog:"
        elif use_c:
            intro = f"Here are top-rated recommendations for **{use_c.replace('_', ' ')}** from our catalog:"
        elif max_p:
            intro = f"Here are the best **{p_type}** options under **₹{max_p:,.0f}** from our catalog:"
        elif intent.get('min_rating'):
            intro = f"Here are highly rated **{p_type}** options with excellent reviews from our catalog:"
        else:
            intro = f"Based on your query, here are relevant product recommendations from our MySQL catalog:"

        items_summary = []
        for p in products[:5]:
            cat_name = p.category.name if p.category else 'N/A'
            items_summary.append(
                f"• **{p.name}** ({p.brand}) - **₹{p.normalized_price_inr:,.2f}** | Rating: **{float(p.rating):.1f}★** (Category: {cat_name})"
            )

        summary_text = "\n".join(items_summary)
        return f"{intro}\n\n{summary_text}\n\nClick on any product card below to view details or add it to your cart!"
