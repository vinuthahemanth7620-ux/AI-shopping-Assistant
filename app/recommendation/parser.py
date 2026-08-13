import re
import logging
from sqlalchemy import func
from app import db

logger = logging.getLogger(__name__)

USD_TO_INR = 83.0


class RequirementParser:
    """
    Requirement Parser - Natural Language Requirement Extraction Layer.
    Parses unstructured user query text into structured shopping preferences:
    - product_type / category
    - use_case
    - max_price / min_price (in INR)
    - min_rating
    - quality_preference
    - brand
    - feature_keywords
    - sort_preference
    - accessory_info
    """

    # Category taxonomy map with primary keywords & disqualifying accessories
    CATEGORY_TAXONOMY = {
        'cooktop': {
            'cat_ids': [10, 9, 37],
            'primary_terms': [
                'induction', 'cooktop', 'induction stove', 'induction cooktop', 'induction cooker',
                'induction hob', 'electric stove', 'electric cooktop', 'gas stove', 'stove', 'cooker',
                'cooking without gas', 'cast iron grill', 'grill topper', 'hot plate', 'burner'
            ],
            'disqualifying_accessories': [
                'knob', 'cover', 'protector', 'cleaning', 'mat', 'pad', 'cord', 'organizer', 'rack',
                'holder', 'stand', 'pan', 'pot', 'spatula', 'spoon', 'towel', 'cleaner'
            ]
        },
        'mixer_grinder': {
            'cat_ids': [10, 9],
            'primary_terms': [
                'mixer', 'grinder', 'mixer grinder', 'blender', 'juicer', 'food processor',
                'hand blender', 'electric blender', 'meat shredder', 'chopper'
            ],
            'disqualifying_accessories': [
                'replacement blade', 'jar lid', 'gasket', 'ring', 'pestle', 'nail grinder',
                'pet grinder', 'dust cover', 'mat', 'organizer'
            ]
        },
        'washing_machine': {
            'cat_ids': [10, 9, 37],
            'primary_terms': [
                'washing machine', 'washer', 'laundry machine', 'clothes washer', 'dryer', 'spin dryer'
            ],
            'disqualifying_accessories': [
                'hose', 'pipe', 'cover', 'inlet pipe', 'drain hose', 'cleaner', 'tablet',
                'vibration pad', 'foot pad', 'door lock', 'lint filter', 'pet hair remover'
            ]
        },
        'microwave': {
            'cat_ids': [10, 9, 38],
            'primary_terms': [
                'microwave', 'microwave oven', 'oven', 'air fryer', 'toaster oven', 'convection oven'
            ],
            'disqualifying_accessories': [
                'glass plate', 'turntable', 'cover', 'rack', 'light bulb', 'fuse', 'handle',
                'cake decoration', 'birthday cake', 'decorations set'
            ]
        },
        'office_chair': {
            'cat_ids': [9, 37, 31],
            'primary_terms': [
                'chair', 'office chair', 'desk chair', 'ergonomic chair', 'swivel chair',
                'gaming chair', 'executive chair', 'patio chair', 'rocking chair', 'recliner', 'armchair'
            ],
            'disqualifying_accessories': [
                'chair cover', 'seat cushion', 'cushion', 'wheel', 'caster', 'armrest cover',
                'slipcover', 'chair mat', 'chair pad', 'footrest', 'chair leg caps'
            ]
        },
        'laptop': {
            'cat_ids': [1, 20],
            'primary_terms': [
                'laptop', 'laptops', 'notebook', 'notebooks', 'macbook', 'chromebook',
                'ultrabook', 'thinkpad', 'ideapad', 'pavilion', 'aspire', 'legion',
                'zenbook', 'vivobook', 'inspiron', 'latitude', 'convertible', 'xps',
                'zephyrus', 'surface pro'
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
            'cat_ids': [2, 17],
            'primary_terms': [
                'phone', 'phones', 'mobile', 'mobiles', 'smartphone', 'smartphones',
                'cellphone', 'cellphones', 'iphone', 'galaxy', 'pixel', 'redmi', 'oneplus', 'android'
            ],
            'disqualifying_accessories': [
                'phone case', 'phone cover', 'screen protector', 'tempered glass', 'phone charger',
                'charging cable', 'phone holder', 'car mount', 'phone mount', 'lanyard',
                'replacement battery', 'repair kit', 'stylus pen', 'phone skin', 'wallet case',
                'holster', 'ring holder', 'selfie stick', 'adapter converter', 'camera bracket',
                'adapter bracket', 'portable charger', 'power bank', 'phone grip', 'magnetic phone grip',
                'smart watch', 'smartwatch'
            ]
        },
        'headphone': {
            'cat_ids': [3, 28, 33, 17],
            'primary_terms': [
                'headphone', 'headphones', 'earphone', 'earphones', 'earbud', 'earbuds',
                'headset', 'headsets', 'airpods', 'aonic', 'soundcore', 'bose quietcomfort', 'sennheiser'
            ],
            'disqualifying_accessories': [
                'headphone case', 'headphone cover', 'headphone stand', 'headphone holder',
                'headphone hanger', 'eartips', 'ear pads', 'headphone cushion', 'headphone cable',
                'replacement cable', 'upgraded cable', 'earphone cable', 'audio cable',
                'audio adapter', 'headphone amp', 'headphone amplifier', 'dust plug', 'cleaner kit'
            ]
        },
        'watch': {
            'cat_ids': [4, 5, 7],
            'primary_terms': ['watch', 'watches', 'smartwatch', 'smartwatches', 'fitbit', 'timepiece', 'chronograph'],
            'disqualifying_accessories': [
                'watch band', 'watch strap', 'watchband', 'watch bezel', 'screen protector',
                'watch charger', 'charging cable', 'watch case', 'watch stand', 'watch winder', 'candle', 'lamp'
            ]
        },
        'shoe': {
            'cat_ids': [5, 35],
            'primary_terms': [
                'shoe', 'shoes', 'sneaker', 'sneakers', 'footwear', 'running shoe', 'running shoes',
                'athletic shoe', 'athletic shoes', 'jogging shoe', 'walking shoe'
            ],
            'disqualifying_accessories': [
                'necklace', 'pendant', 'ring', 'earrings', 'jewelry', 't-shirt', 'shirt', 'pants',
                'socks', 'shoelace', 'insole', 'shoe horn', 'shoe tree', 'shoe polish', 'cleaner',
                'shoe bag', 'towel', 'keychain', 'charm', 'cosplay costume', 'sandal', 'sandals',
                'slipper', 'slippers', 'pump', 'heels', 'high heel', 'boot', 'boots', 'ankle boot'
            ]
        },
        'camera': {
            'cat_ids': [15],
            'primary_terms': [
                'camera', 'cameras', 'dslr', 'camcorder', 'action camera', 'dash cam',
                'mirrorless camera', 'digital camera', 'vlogging camera'
            ],
            'disqualifying_accessories': [
                'backdrop', 'background', 'camera bag', 'camera case', 'camera strap', 'tripod',
                'monopod', 'camera lens', 'lens filter', 'cleaning kit', 'camera battery',
                'camera charger', 'sd card', 'memory card', 'camera mount', 'camera bracket',
                'cage', 'ring light', 'softbox', 'screen protector', 'security camera nvr'
            ]
        },
        'gaming': {
            'cat_ids': [39, 20, 7],
            'primary_terms': [
                'gaming', 'game', 'gamer', 'playstation', 'xbox', 'nintendo', 'console',
                'controller', 'gamepad', 'rtx', 'gpu', 'gaming laptop', 'gaming desktop',
                'gaming monitor', 'gaming headset', 'gaming mouse'
            ],
            'disqualifying_accessories': ['door lock', 'caulking', 'cylinder']
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

    _BRANDS_CACHE = None

    @classmethod
    def get_cached_brands(cls):
        """Cache active product brands for fast matching."""
        if cls._BRANDS_CACHE is None:
            try:
                from app.models.product import Product
                b_rows = db.session.query(Product.brand).filter(Product.is_active == True).distinct().all()
                cls._BRANDS_CACHE = [b[0] for b in b_rows if b[0] and len(b[0]) >= 2]
            except Exception as e:
                logger.error(f"Error caching brands: {str(e)}")
                return []
        return cls._BRANDS_CACHE

    @classmethod
    def extract_requirements(cls, query_text, conversation_history=None):
        """
        Extract normalized shopping requirements from query string.
        Returns a dictionary of parsed requirements.
        """
        q_raw = query_text.strip()
        q_clean = q_raw.lower()

        req = {
            'original_query': q_raw,
            'product_type': None,
            'use_case': None,
            'category_ids': [],
            'max_price': None,
            'min_price': None,
            'min_rating': None,
            'quality_preference': 'standard',
            'brand': None,
            'feature_keywords': [],
            'sort_preference': 'recommended',
            'is_primary_request': True,
            'is_accessory_request': False,
            'target_accessory': None,
            'is_followup': False
        }

        # 1. Parse tokens & feature keywords
        stop_words = {
            'i', 'need', 'show', 'me', 'find', 'suggest', 'give', 'a', 'an', 'the', 'for', 'with',
            'under', 'below', 'less', 'than', 'between', 'and', 'my', 'best', 'good', 'top', 'rated',
            'highly', 'which', 'what', 'product', 'products', 'something', 'one', 'items', 'item',
            'recommend', 'looking', 'want', 'please', 'can', 'you', 'have', 'do', 'in', 'of', 'on', 'at', 'buy', 'now'
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

        # 3. Detect Price / Budget Constraints
        range_match = re.search(r'between\s*₹?\s*(\d+(?:,\d+)*(?:\.\d+)?k?)\s*and\s*₹?\s*(\d+(?:,\d+)*(?:\.\d+)?k?)', q_clean)
        if range_match:
            min_v = cls._parse_number(range_match.group(1))
            max_v = cls._parse_number(range_match.group(2))
            if min_v and max_v:
                req['min_price'] = min_v
                req['max_price'] = max_v

        if req['max_price'] is None:
            budget_patterns = [
                r'(?:under|below|less than|within|max|up to|budget of|around|spend)\s*₹?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(k|thousand|lakh)?',
                r'₹\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(k|thousand|lakh)?',
                r'(\d+)\s*(?:k|thousand)\s*(?:rupees|rs|inr)?'
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

        if any(term in q_clean for term in ['cheap', 'cheapest', 'affordable', 'budget', 'low price', 'lowest price']):
            req['quality_preference'] = 'affordable'
            if req['sort_preference'] == 'recommended':
                req['sort_preference'] = 'price_asc'
        elif any(term in q_clean for term in ['premium', 'expensive', 'flagship', 'high end']):
            req['quality_preference'] = 'premium'
            if req['sort_preference'] == 'recommended':
                req['sort_preference'] = 'price_desc'

        # 5. Product Category Match via Taxonomy & Dynamic MySQL Categories
        matched_tax = []
        for p_type, tax_info in cls.CATEGORY_TAXONOMY.items():
            for p_term in tax_info['primary_terms']:
                if re.search(r'\b' + re.escape(p_term) + r'\b', q_clean):
                    matched_tax.append(p_type)
                    for cid in tax_info['cat_ids']:
                        if cid not in req['category_ids']:
                            req['category_ids'].append(cid)
                    break

        if matched_tax:
            req['product_type'] = matched_tax[0]

        # Dynamic MySQL Category Lookup
        try:
            from app.models.category import Category
            active_db_cats = Category.query.filter_by(is_active=True).all()
            for db_cat in active_db_cats:
                c_name_clean = db_cat.name.lower()
                c_slug_clean = db_cat.slug.replace('-', ' ').lower()
                # Check if query contains category name or slug words
                if (c_name_clean in q_clean or c_slug_clean in q_clean) and db_cat.id not in req['category_ids']:
                    req['category_ids'].append(db_cat.id)
                    if not req['product_type']:
                        req['product_type'] = db_cat.slug.split('-')[0]
        except Exception:
            pass

        # 6. Use Case Detection & Keyword Mapping
        if 'programming' in q_clean or 'coding' in q_clean or 'developer' in q_clean:
            req['use_case'] = 'programming'
            if not req['product_type'] and not req['is_accessory_request']:
                req['product_type'] = 'laptop'
                req['category_ids'] = [1, 20]

        elif 'photography' in q_clean or 'photo' in q_clean or 'camera' in q_clean or 'vlog' in q_clean:
            req['use_case'] = 'photography'
            if not req['product_type'] and not req['is_accessory_request']:
                req['product_type'] = 'camera'
                req['category_ids'] = [15]

        elif 'running' in q_clean or 'runner' in q_clean or 'jogging' in q_clean or 'marathon' in q_clean:
            req['use_case'] = 'running'
            if not req['product_type'] and not req['is_accessory_request']:
                req['product_type'] = 'shoe'
                req['category_ids'] = [5, 35]

        elif 'cooking' in q_clean or 'cook' in q_clean or 'kitchen' in q_clean or 'home' in q_clean or 'appliance' in q_clean:
            req['use_case'] = 'cooking'
            if not req['product_type'] and not req['is_accessory_request']:
                req['product_type'] = 'appliance'
                req['category_ids'] = [10, 9]

        elif 'gift' in q_clean or 'present' in q_clean or 'sister' in q_clean or 'mother' in q_clean or 'friend' in q_clean or 'birthday' in q_clean:
            req['use_case'] = 'gift'
            if not req['category_ids']:
                req['category_ids'] = [5, 6, 9, 27, 4, 3]

        elif 'college' in q_clean or 'student' in q_clean or 'school' in q_clean or 'study' in q_clean or 'backpack' in q_clean:
            req['use_case'] = 'college'
            if not req['category_ids']:
                req['category_ids'] = [1, 20, 3, 31, 5]

        elif 'travel' in q_clean or 'trip' in q_clean or 'vacation' in q_clean:
            req['use_case'] = 'travel'
            if not req['category_ids']:
                req['category_ids'] = [5, 3, 15, 35]

        elif 'gaming' in q_clean or 'gamer' in q_clean:
            req['use_case'] = 'gaming'
            if not req['product_type'] and not req['is_accessory_request']:
                req['product_type'] = 'gaming'
                req['category_ids'] = [39, 20, 7]

        # 7. Multi-turn Follow-up Handling (Strictly gated to true follow-up phrases)
        if conversation_history and not req['product_type'] and not req['category_ids']:
            is_short = len(q_clean.split()) <= 4
            followup_phrases = ['which one', 'which is best', 'cheaper', 'more expensive', 'in black', 'show more']
            if is_short and any(fp in q_clean for fp in followup_phrases):
                for past in reversed(conversation_history):
                    past_q = past.get('user_message', '')
                    if past_q:
                        past_req = cls.extract_requirements(past_q)
                        if past_req.get('product_type'):
                            req['product_type'] = past_req['product_type']
                            req['category_ids'] = past_req['category_ids']
                            req['is_followup'] = True
                            if past_req.get('max_price') is not None and req['max_price'] is None:
                                req['max_price'] = past_req['max_price']
                            break

        # 8. Brand Matching
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
