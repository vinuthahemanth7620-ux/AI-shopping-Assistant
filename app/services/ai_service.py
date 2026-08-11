import os
import re
import json
import logging
import google.generativeai as genai
from flask import current_app, session
from sqlalchemy import or_, and_, func, cast, String
from app import db
from app.models.product import Product
from app.models.category import Category

logger = logging.getLogger(__name__)

# Approximate exchange rate for budget scaling between INR and USD dataset items
USD_TO_INR = 83.0


class AIService:
    """
    AI Service Layer - Handles natural language understanding, database product context retrieval,
    Gemini API prompt engineering, multi-turn context, and response generation.
    Strictly follows MVP architecture.
    """

    # -------------------------------------------------------------------------
    # 1. SEMANTIC CONCEPT & USE-CASE DICTIONARIES
    # -------------------------------------------------------------------------
    ALL_ACCESSORY_TERMS = [
        'mouse', 'mice', 'keyboard', 'keyboards', 'bag', 'bags', 'sleeve', 'sleeves',
        'stand', 'stands', 'charger', 'chargers', 'cooling pad', 'hub', 'docking station',
        'case', 'cases', 'cover', 'covers', 'protector', 'protectors', 'adapter', 'adapters',
        'cable', 'cables', 'holder', 'holders', 'mount', 'mounts', 'strap', 'straps', 'skin',
        'skins', 'insole', 'insoles', 'shoelace', 'shoelaces', 'cleaner', 'polish', 'filter',
        'tripod', 'tripods', 'lens', 'lenses', 'memory card', 'sd card', 'bezel', 'ring',
        'glove', 'rack', 'mat', 'organizer', 'hinge', 'knob', 'lid', 'lids', 'ram', 'memory',
        'drive', 'thumb drive', 'flash drive', 'tracker', 'grip', 'display', 'screen', 'lcd',
        'motherboard', 'housing', 'replacement', 'battery', 'power bank', 'portable', 'compatible', 'part'
    ]

    SEMANTIC_CONCEPT_MAP = {
        'phone': {
            'primary_types': ['phone', 'smartphone', 'mobile', 'cellphone', 'iphone', 'galaxy', 'pixel', 'redmi', 'oneplus', 'android'],
            'primary_categories': ['Mobiles'],
            'secondary_categories': ['Cell Phones & Accessories'],
            'primary_keywords': ['phone', 'mobile', 'smartphone', 'cell', '5g', 'android', 'iphone', 'galaxy', 'pro', 'ultra', 'pixel'],
            'accessories': ['case', 'cases', 'cover', 'covers', 'screen protector', 'protector', 'charger', 'chargers', 'cable', 'cables', 'holder', 'holders', 'mount', 'mounts', 'adapter', 'skin', 'skins', 'strap', 'ring holder', 'car mount']
        },
        'laptop': {
            'primary_types': ['laptop', 'notebook', 'macbook', 'chromebook', 'envy', 'ideapad', 'thinkpad', 'pavilion', 'spectre', 'legion', 'zenbook', 'vivobook', 'aspire', 'inspiron', 'latitude'],
            'primary_categories': ['Laptops'],
            'secondary_categories': ['Computers'],
            'primary_keywords': ['laptop', 'notebook', 'macbook', 'chromebook', 'envy', 'ideapad', 'thinkpad', 'pavilion', 'spectre', 'legion', 'zenbook', 'vivobook', 'aspire', 'inspiron', 'latitude'],
            'accessories': ['mouse', 'mice', 'keyboard', 'keyboards', 'bag', 'bags', 'sleeve', 'sleeves', 'stand', 'stands', 'charger', 'chargers', 'cooling pad', 'usb hub', 'hub', 'docking station', 'screen protector', 'case', 'cover', 'adapter', 'cable']
        },
        'headphone': {
            'primary_types': ['headphone', 'earphone', 'earbud', 'headset', 'airpods'],
            'primary_categories': ['Headphones'],
            'secondary_categories': ['Portable Audio & Accessories', 'Home Audio & Theater'],
            'primary_keywords': ['headphone', 'earphone', 'earbud', 'headset', 'airpods', 'audio', 'noise canceling'],
            'accessories': ['case', 'cases', 'ear pads', 'eartips', 'cable', 'cables', 'adapter', 'headphone stand']
        },
        'watch': {
            'primary_types': ['watch', 'smartwatch', 'fitbit'],
            'primary_categories': ['Smart Watches'],
            'secondary_categories': [],
            'primary_keywords': ['watch', 'smartwatch', 'fitness watch', 'fitbit'],
            'accessories': ['band', 'bands', 'strap', 'straps', 'screen protector', 'case', 'charger', 'cable', 'bezel']
        },
        'camera': {
            'primary_types': ['camera', 'dslr', 'camcorder'],
            'primary_categories': ['Camera & Photo'],
            'secondary_categories': [],
            'primary_keywords': ['camera', 'dslr', 'camcorder', 'action camera', 'dash cam'],
            'accessories': ['lens', 'lenses', 'tripod', 'tripods', 'bag', 'bags', 'battery', 'memory card', 'sd card', 'filter', 'flash', 'strap', 'mount', 'cap', 'hood', 'case', 'adapter']
        },
        'shoe': {
            'primary_types': ['shoe', 'shoes', 'footwear', 'sneaker', 'boot', 'sandal'],
            'primary_categories': ['AMAZON FASHION', 'Sports & Outdoors'],
            'secondary_categories': [],
            'primary_keywords': ['shoe', 'shoes', 'footwear', 'sneaker', 'boot', 'running shoe'],
            'accessories': ['insole', 'insoles', 'shoelace', 'shoelaces', 'shoe horn', 'cleaner', 'polish', 'tree', 'socks']
        },
        'kitchen': {
            'primary_types': ['kitchen', 'cooking', 'cookware', 'appliance', 'oven', 'mixer', 'blender', 'air fryer'],
            'primary_categories': ['Appliances', 'Amazon Home', 'Tools & Home Improvement'],
            'secondary_categories': [],
            'primary_keywords': ['kitchen', 'cookware', 'mixer', 'blender', 'oven', 'air fryer', 'pot', 'pan'],
            'accessories': ['sponge', 'towel', 'cleaner', 'rack', 'mat', 'organizer', 'glove']
        },
        'tv': {
            'primary_types': ['tv', 'television', 'monitor', 'display'],
            'primary_categories': ['Home Audio & Theater', 'Computers', 'All Electronics'],
            'secondary_categories': [],
            'primary_keywords': ['tv', 'television', 'monitor', '4k tv', 'oled tv', 'led tv'],
            'accessories': ['wall mount', 'mount', 'tv stand', 'stand', 'remote', 'hdmi cable', 'cable', 'bracket']
        }
    }

    USE_CASE_MAP = {
        'photography': {
            'triggers': ['photography', 'camera', 'photo', 'pictures', 'photos', 'portrait', 'shots'],
            'concepts': ['phone', 'camera'],
            'keywords': ['camera', 'photography', 'photo', 'lens', 'megapixel', 'sensor', 'zoom']
        },
        'programming': {
            'triggers': ['programming', 'coding', 'developer', 'code', 'software development', 'program'],
            'concepts': ['laptop'],
            'keywords': ['laptop', 'ram', 'processor', 'ssd', 'intel', 'ryzen', 'm3', 'i7', 'i9', '16gb', '32gb']
        },
        'gaming': {
            'triggers': ['gaming', 'game', 'gamer', 'play games', 'esports'],
            'concepts': ['laptop', 'headphone', 'tv'],
            'keywords': ['gaming', 'rtx', 'gpu', 'graphics', 'hz', 'fps', 'geforce', 'razer', 'rog', 'alienware']
        },
        'online_classes': {
            'triggers': ['online class', 'online classes', 'study', 'student', 'college', 'school', 'zoom', 'education'],
            'concepts': ['laptop', 'headphone', 'phone'],
            'keywords': ['laptop', 'headphone', 'mic', 'webcam', 'tablet', 'battery', 'student', 'study']
        },
        'working_from_home': {
            'triggers': ['work from home', 'working from home', 'wfh', 'home office', 'desk work'],
            'concepts': ['laptop', 'headphone', 'tv', 'kitchen'],
            'keywords': ['laptop', 'chair', 'desk', 'headphone', 'monitor', 'keyboard', 'mouse', 'coffee']
        },
        'cooking': {
            'triggers': ['cooking', 'cook', 'recipe', 'kitchen', 'food prep', 'bake', 'baking'],
            'concepts': ['kitchen'],
            'keywords': ['kitchen', 'cookware', 'mixer', 'blender', 'oven', 'air fryer', 'pot', 'pan', 'utensil']
        },
        'gift': {
            'triggers': ['gift', 'present', 'sister', 'friend', 'brother', 'birthday', 'anniversary'],
            'concepts': ['headphone', 'watch', 'shoe', 'kitchen', 'phone'],
            'keywords': ['gift', 'beauty', 'fashion', 'watch', 'headphone', 'accessory', 'stylish']
        },
        'travel': {
            'triggers': ['travel', 'travelling', 'trip', 'flight', 'portable', 'outdoor', 'vacation'],
            'concepts': ['shoe', 'headphone', 'camera', 'phone'],
            'keywords': ['travel', 'portable', 'bag', 'lightweight', 'wireless', 'durability', 'battery']
        },
        'watching_movies': {
            'triggers': ['watching movies', 'movie', 'cinema', 'shows', 'entertainment', 'video'],
            'concepts': ['tv', 'headphone', 'laptop'],
            'keywords': ['tv', 'theater', 'display', 'screen', 'audio', 'sound', 'oled', 'hdr', 'noise']
        }
    }

    @staticmethod
    def get_api_key():
        """Retrieve Gemini API key safely from Flask config or environment variables."""
        try:
            key = current_app.config.get('GEMINI_API_KEY') if current_app else os.getenv('GEMINI_API_KEY')
            return key.strip() if key else ''
        except Exception as e:
            logger.error(f"Error fetching GEMINI_API_KEY: {str(e)}")
            return ''

    _BRANDS_CACHE = None

    @classmethod
    def get_cached_brands(cls):
        """Cache active product brands in memory for instant intent matching."""
        if cls._BRANDS_CACHE is None:
            try:
                b_rows = db.session.query(Product.brand).filter(Product.is_active == True).distinct().all()
                cls._BRANDS_CACHE = [b[0] for b in b_rows if b[0] and len(b[0]) >= 2]
            except Exception as e:
                logger.error(f"Error caching brands: {str(e)}")
                return []
        return cls._BRANDS_CACHE

    # -------------------------------------------------------------------------
    # 2. NATURAL LANGUAGE INTENT EXTRACTION
    # -------------------------------------------------------------------------
    @classmethod
    def extract_user_intent(cls, user_query, conversation_history=None):
        """
        Extract structured shopping intent from user query:
        - product_type: Primary product concept ('phone', 'laptop', 'headphone', etc.)
        - use_case: Targeted activity ('photography', 'programming', 'gaming', etc.)
        - category_ids: List of database Category IDs matching intent
        - category_names: List of category names
        - max_price / min_price: Extracted numeric budget limits (in INR)
        - brand: Specific brand if mentioned
        - min_rating: Rating constraint (e.g., 4.0)
        - sort_preference: 'recommended', 'rating', 'price_asc', 'price_desc'
        - keywords: Extracted feature / search keywords
        - is_followup: True if query depends on previous conversation turn
        - is_primary_request: True if query requests a core device/item
        - is_accessory_request: True if query explicitly requests an accessory
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
            'keywords': [],
            'sort_preference': 'recommended',
            'query_type': 'general',
            'is_followup': False,
            'is_primary_request': False,
            'is_accessory_request': False,
            'target_accessory': None,
            'original_query': user_query
        }

        # Step A: Check if query explicitly asks for an accessory (e.g., "mouse for my laptop", "laptop bag", "phone case")
        for acc in cls.ALL_ACCESSORY_TERMS:
            if re.search(r'\b' + re.escape(acc) + r's?\b', query_text):
                intent['is_accessory_request'] = True
                intent['target_accessory'] = acc
                intent['keywords'].append(acc)
                break

        # Check for conversational follow-up triggers
        followup_triggers = [
            'which one', 'which is best', 'cheaper', 'expensive',
            'higher rating', 'best rated of these', 'top rated of these', 'recommend from these'
        ]

        # Step B: Detect Primary Product Concept / Type explicitly mentioned in query
        for concept, data in cls.SEMANTIC_CONCEPT_MAP.items():
            types_to_check = data.get('primary_types', [])
            for t in types_to_check:
                if re.search(r'\b' + re.escape(t) + r's?\b', query_text):
                    intent['product_type'] = concept
                    break
            if intent['product_type']:
                break

        # If product type wasn't explicitly mentioned, check if query is a follow-up referencing previous turn
        if not intent['product_type']:
            if any(trig in query_text for trig in followup_triggers) or len(query_text.split()) <= 4:
                if conversation_history:
                    for past in reversed(conversation_history):
                        past_q = past.get('user_message', '').strip()
                        if past_q:
                            past_intent = cls._quick_parse_concepts(past_q)
                            if past_intent.get('product_type'):
                                intent['product_type'] = past_intent['product_type']
                                intent['is_followup'] = True
                                intent['is_primary_request'] = past_intent.get('is_primary_request', True)
                                if past_intent.get('max_price') is not None and intent['max_price'] is None:
                                    intent['max_price'] = past_intent['max_price']
                                if past_intent.get('min_price') is not None and intent['min_price'] is None:
                                    intent['min_price'] = past_intent['min_price']
                                break

        # Set Primary vs Accessory Intent Flags
        if intent['product_type'] and not intent['is_accessory_request']:
            intent['is_primary_request'] = True
            intent['query_type'] = 'primary_product'
        elif intent['is_accessory_request']:
            intent['query_type'] = 'accessory'

        # Step C: Detect Use Case (if not an explicit accessory request)
        for u_key, u_data in cls.USE_CASE_MAP.items():
            if any(trig in query_text for trig in u_data['triggers']):
                intent['use_case'] = u_key
                intent['keywords'].extend(u_data['keywords'])
                # If product concept not explicitly specified and not an accessory request, inherit primary concept from use case
                if not intent['product_type'] and not intent['is_accessory_request'] and u_data['concepts']:
                    intent['product_type'] = u_data['concepts'][0]
                break

        # Step D: Resolve Category IDs based on Product Concept
        if intent['product_type'] and intent['product_type'] in cls.SEMANTIC_CONCEPT_MAP:
            concept_info = cls.SEMANTIC_CONCEPT_MAP[intent['product_type']]
            target_cats = concept_info['primary_categories'] + concept_info.get('secondary_categories', [])
            intent['keywords'].extend(concept_info['primary_keywords'])
            for cname in target_cats:
                cats = Category.query.filter(Category.name.ilike(f"%{cname}%")).all()
                for c in cats:
                    if c.id not in intent['category_ids']:
                        intent['category_ids'].append(c.id)
                        intent['category_names'].append(c.name)

        # If explicit accessory request, search across all categories containing products matching accessory term
        if intent.get('is_accessory_request') and intent.get('target_accessory'):
            acc_term = intent['target_accessory']
            acc_prods = Product.query.filter(Product.is_active == True, Product.name.ilike(f"%{acc_term}%")).limit(30).all()
            for ap in acc_prods:
                if ap.category_id not in intent['category_ids']:
                    intent['category_ids'].append(ap.category_id)

        # Direct DB category matching fallback if no category resolved yet
        if not intent['category_ids']:
            all_cats = Category.query.filter_by(is_active=True).all()
            for cat in all_cats:
                cname = cat.name.lower()
                c_sing = cname[:-1] if cname.endswith('s') else cname
                if cname in query_text or c_sing in query_text:
                    intent['category_ids'].append(cat.id)
                    intent['category_names'].append(cat.name)

        # Step E: Detect Price / Budget
        range_match = re.search(r'between\s*₹?\s*(\d+k?)\s*and\s*₹?\s*(\d+k?)', query_text)
        if range_match:
            min_val = cls._parse_number_str(range_match.group(1))
            max_val = cls._parse_number_str(range_match.group(2))
            if min_val and max_val:
                intent['min_price'] = min_val
                intent['max_price'] = max_val
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

        # Step F: Detect Rating Preferences
        rating_terms = ['best rated', 'highest rating', 'top rated', 'high rating', 'most rated', 'good reviews', 'best review']
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

        # Step G: Detect Sort Preferences
        if any(term in query_text for term in ['cheapest', 'affordable', 'budget friendly', 'low price', 'lowest price', 'lowest cost', 'least expensive']):
            intent['sort_preference'] = 'price_asc'
        elif any(term in query_text for term in ['premium', 'expensive', 'high end', 'flagship', 'highest price', 'most expensive', 'highest cost']):
            intent['sort_preference'] = 'price_desc'
        elif any(term in query_text for term in ['best', 'top', 'recommended', 'suggest', 'popular']):
            if intent['sort_preference'] == 'recommended':
                intent['sort_preference'] = 'recommended'

        # Step H: Detect Brand
        brands = cls.get_cached_brands()
        for b_name in brands:
            if b_name and len(b_name) >= 2:
                if re.search(r'\b' + re.escape(b_name.lower()) + r'\b', query_text):
                    intent['brand'] = b_name
                    break

        # Step I: Refine 13-intent taxonomy (query_type)
        if intent.get('is_followup'):
            intent['query_type'] = 'followup'
        elif any(term in query_text for term in ['how many product', 'how many item', 'average rating', 'total products', 'catalog stat', 'dataset stat', 'how many total']):
            intent['query_type'] = 'dataset_query'
        elif any(term in query_text for term in ['what categor', 'which categor', 'how many categor', 'categories do you have', 'categories available']):
            intent['query_type'] = 'category_query'
        elif any(term in query_text for term in ['compare', 'versus', ' vs ', 'difference between', 'which is better']):
            intent['query_type'] = 'product_comparison'
        elif any(term in query_text for term in ['tell me about', 'details of', 'description of', 'specs of', 'specifications of', 'who makes', 'reviews of']):
            intent['query_type'] = 'product_detail'
        elif any(term in query_text for term in ['does it have', 'does this product have', 'has bluetooth', 'has touchscreen', 'has ssd', 'has 5g']):
            intent['query_type'] = 'attribute_query'
        elif any(term in query_text for term in ['what brand', 'which brand', 'brands do you have', 'laptop brands', 'phone brands', 'brand has the most', 'highest-rated brand']):
            intent['query_type'] = 'brand_query'
        elif any(term in query_text for term in ['price of', 'cost of', 'how much is', 'which is cheapest', 'cheapest laptop', 'cheapest phone', 'cheapest product', 'highest price', 'most expensive']):
            intent['query_type'] = 'price_query'
        elif any(term in query_text for term in ['what rating', 'highest rating', 'highest rated', 'best rated', 'most reviews']):
            intent['query_type'] = 'rating_query'
        elif any(term in query_text for term in ['what is ram', 'what is a laptop', 'what is 5g', 'what is bluetooth']):
            intent['query_type'] = 'general_question'
        elif intent.get('max_price') is not None or intent.get('min_price') is not None or intent.get('min_rating') is not None:
            intent['query_type'] = 'filtering'
        elif intent.get('use_case'):
            intent['query_type'] = 'recommendation'
        elif any(term in query_text for term in ['show me', 'which cameras', 'do you have', 'what laptops', 'find me']):
            intent['query_type'] = 'product_search'

        intent['keywords'] = list(dict.fromkeys(intent['keywords']))
        return intent

    # -------------------------------------------------------------------------
    # 2.5 SPECIALIZED DATASET & CATALOG QUERY EXECUTORS
    # -------------------------------------------------------------------------
    @classmethod
    def get_dataset_statistics(cls, query_text):
        """Query actual dataset statistics from MySQL database."""
        q_lower = query_text.lower()

        if any(term in q_lower for term in ['how many product', 'total product', 'items available', 'catalog size', 'products available']):
            total_p = db.session.query(func.count(Product.id)).filter(Product.is_active == True).scalar() or 0
            return f"Our catalog database currently contains **{total_p:,}** active products across various categories."

        if any(term in q_lower for term in ['how many categor', 'total categor', 'categories do you have', 'categories available']):
            total_c = db.session.query(func.count(Category.id)).filter(Category.is_active == True).scalar() or 0
            return f"We have **{total_c}** active product categories available in our database catalog."

        if any(term in q_lower for term in ['average rating', 'avg rating', 'mean rating']):
            avg_r = db.session.query(func.avg(Product.rating)).filter(Product.is_active == True).scalar() or 0.0
            return f"The average customer rating across all catalog products in our database is **{float(avg_r):.2f} / 5.0★**."

        if any(term in q_lower for term in ['category has the most', 'largest category', 'biggest category']):
            top_cat = db.session.query(Category.name, func.count(Product.id).label('total')).join(Product).filter(Product.is_active == True).group_by(Category.name).order_by(db.desc('total')).first()
            if top_cat:
                return f"The category with the most products in our dataset is **{top_cat[0]}** with **{top_cat[1]:,}** products."

        if any(term in q_lower for term in ['brand has the most', 'largest brand', 'most products']):
            top_b = db.session.query(Product.brand, func.count(Product.id).label('total')).filter(Product.is_active == True, Product.brand != '').group_by(Product.brand).order_by(db.desc('total')).first()
            if top_b:
                return f"The brand with the most products in our catalog is **{top_b[0]}** with **{top_b[1]:,}** products."

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
    def get_brand_statistics(cls, intent, query_text):
        """Query actual brand information from MySQL database."""
        q_lower = query_text.lower()
        p_concept = intent.get('product_type')

        if any(term in q_lower for term in ['highest rated brand', 'best brand', 'highest-rated brand']):
            q_b = db.session.query(Product.brand, func.avg(Product.rating).label('avgr')).filter(Product.is_active == True, Product.brand != '')
            if intent.get('category_ids'):
                q_b = q_b.filter(Product.category_id.in_(intent['category_ids']))
            top_b = q_b.group_by(Product.brand).having(func.count(Product.id) >= 2).order_by(db.desc('avgr')).first()
            if top_b:
                concept_str = f" for {p_concept}s" if p_concept else ""
                return f"The highest rated brand{concept_str} in our catalog database is **{top_b[0]}** with an average rating of **{float(top_b[1]):.2f}★**."

        q_brands = db.session.query(Product.brand, func.count(Product.id).label('cnt')).filter(Product.is_active == True, Product.brand != '')
        if intent.get('category_ids'):
            q_brands = q_brands.filter(Product.category_id.in_(intent['category_ids']))
        brand_rows = q_brands.group_by(Product.brand).order_by(db.desc('cnt')).limit(10).all()

        if brand_rows:
            b_list = [f"• **{b[0]}** ({b[1]} products)" for b in brand_rows]
            concept_str = f" **{p_concept}**" if p_concept else ""
            return f"Here are popular{concept_str} brands available in our MySQL catalog:\n\n" + "\n".join(b_list)

        return "No specific brand data found matching your query in our catalog."

    @classmethod
    def get_category_statistics(cls, query_text):
        """Query actual category metadata from MySQL database."""
        cats = db.session.query(Category.name, func.count(Product.id).label('cnt')).join(Product).filter(Category.is_active == True, Product.is_active == True).group_by(Category.name).order_by(db.desc('cnt')).all()
        if cats:
            cat_list = [f"• **{c[0]}** ({c[1]:,} products)" for c in cats[:12]]
            return f"Here are active product categories available in our catalog:\n\n" + "\n".join(cat_list)
        return "No category information found in database."

    @classmethod
    def generate_product_comparison(cls, products, intent=None):
        """Build GFM Markdown comparison table for 2 or more products."""
        if not products or len(products) < 1:
            return "Please specify products to compare."

        prods = products[:4]
        cols = [f"**Product {i}**" for i in range(1, len(prods) + 1)]
        header = "| Attribute | " + " | ".join(cols) + " |"
        separator = "| --- | " + " | ".join(["---"] * len(cols)) + " |"

        row_name = "| **Name** | " + " | ".join([p.name[:35] for p in prods]) + " |"
        row_brand = "| **Brand** | " + " | ".join([p.brand for p in prods]) + " |"
        row_cat = "| **Category** | " + " | ".join([p.category.name if p.category else 'N/A' for p in prods]) + " |"
        row_price = "| **Price** | " + " | ".join([f"₹{cls.get_normalized_price_inr(p):,.2f}" for p in prods]) + " |"
        row_rating = "| **Rating** | " + " | ".join([f"{float(p.rating):.1f}★" for p in prods]) + " |"

        table = "\n".join([header, separator, row_name, row_brand, row_cat, row_price, row_rating])
        return f"Here is a side-by-side comparison based on our MySQL catalog data:\n\n{table}\n\nAll attributes are verified directly from our catalog database."

    @classmethod
    def generate_product_detail_response(cls, product, query_text):
        """Synthesize detailed attribute response for a specific product without hallucination."""
        if not product:
            return "Product not found in catalog."

        q_lower = query_text.lower()
        norm_price = cls.get_normalized_price_inr(product)
        cat_name = product.category.name if product.category else 'N/A'
        specs = product.specifications if isinstance(product.specifications, dict) else {}

        if any(term in q_lower for term in ['price of', 'cost of', 'how much']):
            return f"The price of **{product.name}** is **₹{norm_price:,.2f}**."

        if any(term in q_lower for term in ['rating', 'review', 'stars']):
            return f"**{product.name}** has a customer rating of **{float(product.rating):.1f} / 5.0★** in our catalog."

        # Feature presence check (e.g. Bluetooth, Touchscreen, SSD, 5G)
        feature_keywords = ['bluetooth', 'touchscreen', 'ssd', 'camera', 'wireless', '5g', 'hdmi', '4k', 'oled']
        for feat in feature_keywords:
            if feat in q_lower:
                text_to_search = (product.name + ' ' + (product.description or '') + ' ' + json.dumps(specs)).lower()
                if feat in text_to_search:
                    return f"Yes! **{product.name}** includes **{feat.upper()}** feature based on our catalog data."
                else:
                    return f"I couldn't find {feat.upper()} specification in the available product data for **{product.name}**."

        specs_formatted = ""
        if specs:
            specs_formatted = "\n**Specifications**:\n" + "\n".join([f"• **{k}**: {v}" for k, v in list(specs.items())[:5] if isinstance(v, (str, int, float))])

        desc_str = f"\n**Description**: {product.description[:250]}..." if product.description else ""

        return (
            f"### {product.name}\n"
            f"• **Brand**: {product.brand}\n"
            f"• **Category**: {cat_name}\n"
            f"• **Price**: ₹{norm_price:,.2f}\n"
            f"• **Rating**: {float(product.rating):.1f} / 5.0★\n"
            f"• **Availability**: {'In Stock (' + str(product.stock_quantity) + ' units)' if product.stock_quantity > 0 else 'In Stock'}"
            f"{desc_str}"
            f"{specs_formatted}"
        )

    @classmethod
    def generate_general_explanation(cls, query_text):
        """Provide clear natural educational explanations for non-dataset general concept questions."""
        q_lower = query_text.lower()
        if 'ram' in q_lower:
            return "RAM (Random Access Memory) is a computer's short-term memory used to store data that the processor needs quickly while running apps and multitasking."
        if 'laptop' in q_lower:
            return "A laptop is a portable personal computer with an integrated screen, keyboard, and rechargeable battery designed for mobile work and entertainment."
        if 'bluetooth' in q_lower:
            return "Bluetooth is a short-range wireless technology standard used for exchanging data between fixed and mobile devices over short distances."
        return "This is a general computer concept. Feel free to ask about available products in our catalog!"

    @classmethod
    def _quick_parse_concepts(cls, text):
        """Helper to parse concept, primary flag, and budget from historical query string."""
        text_lower = text.lower()
        res = {'product_type': None, 'is_primary_request': False, 'max_price': None}
        is_acc = any(re.search(r'\b' + re.escape(acc) + r's?\b', text_lower) for acc in cls.ALL_ACCESSORY_TERMS)

        for concept, data in cls.SEMANTIC_CONCEPT_MAP.items():
            for t in data.get('primary_types', []):
                if re.search(r'\b' + re.escape(t) + r's?\b', text_lower):
                    res['product_type'] = concept
                    res['is_primary_request'] = not is_acc
                    break
            if res['product_type']:
                break

        b_match = re.search(r'(?:under|below|less than|within|max|up to|budget of|around|spend)\s*₹?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(k|thousand|lakh)?', text_lower)
        if not b_match:
            b_match = re.search(r'(\d+)\s*(?:k|thousand)\s*(?:rupees|rs|inr)?', text_lower)
        if b_match:
            raw_num = b_match.group(1).replace(',', '')
            multiplier = b_match.group(2) if len(b_match.groups()) > 1 else None
            try:
                val = float(raw_num)
                if multiplier in ['k', 'thousand']:
                    val *= 1000
                elif multiplier == 'lakh':
                    val *= 100000
                res['max_price'] = val
            except ValueError:
                pass

        return res

    @staticmethod
    def _parse_number_str(val_str):
        """Helper to parse strings like '20k', '50000', '15' into float."""
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
    def get_normalized_price_inr(cls, product):
        """
        Unified price normalizer: Converts USD prices to INR for imported Amazon dataset products.
        Seed products (Category IDs 1-4) or items with raw price >= 3000 are in INR.
        Imported products (Category IDs 5-39 with raw price < 3000) are in USD -> price * 83.0.
        """
        if not product or product.price is None:
            return 0.0
        raw_price = float(product.price)
        cat_id = product.category_id or 0
        if cat_id <= 4 or raw_price >= 3000.0:
            return raw_price
        return raw_price * USD_TO_INR

    @classmethod
    def validate_product_relevance(cls, product, intent):
        """
        Final validation filter to enforce positive & negative product relevance AND strict budget limits.
        Guarantees that accessories/unrelated items and products exceeding max_price are strictly purged.
        """
        if not product:
            return False

        p_name_lower = product.name.lower()
        cat_name = product.category.name if product.category else ''
        p_concept = intent.get('product_type')
        is_acc_req = intent.get('is_accessory_request', False)
        is_prim_req = intent.get('is_primary_request', False)

        # 1. HARD BUDGET ENFORCEMENT
        norm_price = cls.get_normalized_price_inr(product)
        if intent.get('max_price') is not None:
            if norm_price > float(intent['max_price']):
                return False  # HARD REJECT IF NORMALIZED PRICE EXCEEDS EXPLICIT BUDGET!

        if intent.get('min_price') is not None:
            if norm_price < float(intent['min_price']):
                return False

        # 2. Primary Product Relevance Enforcement
        if is_prim_req and p_concept and p_concept in cls.SEMANTIC_CONCEPT_MAP:
            concept_info = cls.SEMANTIC_CONCEPT_MAP[p_concept]
            prim_kws = concept_info.get('primary_keywords', [])
            prim_types = concept_info.get('primary_types', [])

            has_primary_identity = any(re.search(r'\b' + re.escape(pk) + r's?\b', p_name_lower) for pk in (prim_kws + prim_types))

            # REJECT if product is outside primary category AND does not explicitly state primary product identity
            prim_cats = concept_info.get('primary_categories', [])
            if prim_cats and cat_name not in prim_cats and not has_primary_identity:
                return False

            acc_list = concept_info.get('accessories', []) + cls.ALL_ACCESSORY_TERMS
            acc_list_filtered = [acc for acc in acc_list if acc not in prim_kws and acc not in prim_types]

            # If product explicitly has primary identity (e.g. "Acer Aspire Laptop 8GB RAM"), do not reject because of embedded spec words or bundle phrases
            if has_primary_identity:
                spec_words = ['ram', 'memory', 'display', 'screen', 'lcd', 'drive', 'battery', 'portable', 'accessory', 'accessories']
                acc_list_filtered = [acc for acc in acc_list_filtered if acc not in spec_words]

            # REJECT if product name contains any accessory term
            for acc in acc_list_filtered:
                if re.search(r'\b' + re.escape(acc) + r's?\b', p_name_lower):
                    return False

        # 3. Explicit Accessory Request Enforcement
        elif is_acc_req:
            target_acc = intent.get('target_accessory')
            if target_acc and not re.search(r'\b' + re.escape(target_acc) + r's?\b', p_name_lower):
                return False

        return True

    # -------------------------------------------------------------------------
    # 3. MULTI-LEVEL DATABASE RETRIEVAL ENGINE
    # -------------------------------------------------------------------------
    @classmethod
    def retrieve_relevant_products(cls, intent, user_query, limit=8):
        """
        Execute multi-level SQLAlchemy retrieval strategy:
        LEVEL 1: Category ID & Primary Product Name filtering.
        LEVEL 2: Description text ILIKE matching.
        LEVEL 3: Specifications JSON text matching.
        LEVEL 4: Semantic term expansion.
        LEVEL 5: Budget & Rating filtering (with strict INR/USD dual-currency normalization).
        LEVEL 6: Candidate scoring & relevance validation.
        """
        query_text = user_query.strip().lower()

        # Debug Logging
        logger.info("=" * 60)
        logger.info(f"[AI PIPELINE LOG] Original User Query: {user_query}")
        logger.info(f"[AI PIPELINE LOG] Extracted Intent: product_type={intent.get('product_type')}, is_primary_req={intent.get('is_primary_request')}, is_accessory_req={intent.get('is_accessory_request')}, target_accessory={intent.get('target_accessory')}, budget_max={intent.get('max_price')}, categories={intent.get('category_names')}")
        logger.info(f"[AI PIPELINE LOG] Keywords: {intent.get('keywords')}")

        # Base active product query
        base_query = Product.query.filter(Product.is_active == True, Product.is_available == True)

        # ---------------------------------------------------------
        # LEVEL 1 & LEVEL 5: Apply Category & Price Filters
        # ---------------------------------------------------------
        q = base_query

        # Apply Category Filter if available (Indexed!)
        if intent.get('category_ids'):
            q = q.filter(Product.category_id.in_(intent['category_ids']))

        # Apply Strict Dual-Currency Price Filter
        max_p = intent.get('max_price')
        min_p = intent.get('min_price')

        if max_p is not None:
            usd_max = max_p / USD_TO_INR
            q = q.filter(
                or_(
                    and_(Product.category_id <= 4, Product.price <= max_p),
                    and_(Product.category_id > 4, Product.price <= usd_max)
                )
            )

        if min_p is not None:
            usd_min = min_p / USD_TO_INR
            q = q.filter(
                or_(
                    and_(Product.category_id <= 4, Product.price >= min_p),
                    and_(Product.category_id > 4, Product.price >= usd_min)
                )
            )

        # Apply Rating Filter
        if intent.get('min_rating') is not None:
            q = q.filter(Product.rating >= intent['min_rating'])

        # Apply Brand Filter
        if intent.get('brand'):
            q = q.filter(Product.brand.ilike(f"%{intent['brand']}%"))

        # HARD SQL EXCLUSION of Accessories when user explicitly asks for a primary product
        if intent.get('is_primary_request') and intent.get('product_type') and intent['product_type'] in cls.SEMANTIC_CONCEPT_MAP:
            concept_info = cls.SEMANTIC_CONCEPT_MAP[intent['product_type']]
            acc_list = concept_info.get('accessories', [])
            for acc_term in acc_list[:8]:
                q = q.filter(~Product.name.ilike(f"%{acc_term}%"))

        # ---------------------------------------------------------
        # LEVEL 2 & 3: Keyword Search across Name & Description
        # ---------------------------------------------------------
        query_words = [w for w in user_query.lower().split() if len(w) >= 3 and w not in ['show', 'tell', 'about', 'with', 'from', 'have', 'this', 'product', 'that', 'what', 'which', 'laptop', 'phone', 'price']]
        keywords = intent.get('keywords', [])
        candidates = []

        or_clauses = []
        for qw in query_words:
            term = f"%{qw}%"
            or_clauses.append(Product.name.ilike(term))

        for kw in keywords[:5]:
            term = f"%{kw}%"
            or_clauses.append(Product.name.ilike(term))
            or_clauses.append(Product.description.ilike(term))

        if or_clauses:
            kw_query = q.filter(or_(*or_clauses)).order_by(Product.rating.desc())
            candidates = kw_query.limit(50).all()

        if not candidates:
            candidates = q.order_by(Product.rating.desc()).limit(40).all()

        # ---------------------------------------------------------
        # NO-RESULT FALLBACK (STRICT BUDGET PRESERVATION)
        # ---------------------------------------------------------
        if not candidates:
            logger.info("[AI PIPELINE LOG] Strict query produced 0 matches.")
            intent['relaxed_search'] = True

            # DO NOT expand max_price budget if explicitly specified!
            if max_p is None:
                q_relaxed = base_query
                if intent.get('category_ids'):
                    q_relaxed = q_relaxed.filter(Product.category_id.in_(intent['category_ids']))
                candidates = q_relaxed.order_by(Product.rating.desc()).limit(30).all()

        # ---------------------------------------------------------
        # LEVEL 6: Scoring & Composite Ranking Strategy
        # ---------------------------------------------------------
        scored_products = []
        for p in candidates:
            score = float(p.rating or 0.0) * 20.0

            p_name_lower = p.name.lower()
            cat_name = p.category.name if p.category else ''
            norm_p = cls.get_normalized_price_inr(p)

            p_concept = intent.get('product_type')
            concept_info = cls.SEMANTIC_CONCEPT_MAP.get(p_concept, {}) if p_concept else {}

            # Primary Category Boost (+500 points)
            prim_cats = concept_info.get('primary_categories', [])
            if prim_cats and cat_name in prim_cats:
                score += 500.0

            # Boost for primary product keyword in name (+300 points)
            if p_concept:
                prim_kws = concept_info.get('primary_keywords', [])
                if any(kw in p_name_lower for kw in prim_kws):
                    score += 300.0

            # Massive Penalty for Accessories if user requested a primary product
            if intent.get('is_primary_request') and p_concept:
                acc_list = concept_info.get('accessories', []) + cls.ALL_ACCESSORY_TERMS
                if any(acc in p_name_lower for acc in acc_list):
                    score -= 10000.0

            # Boost for explicit accessory match if accessory requested
            if intent.get('is_accessory_request'):
                target_acc = intent.get('target_accessory')
                if target_acc and target_acc in p_name_lower:
                    score += 500.0

            # Boost for use-case keyword matches
            if intent.get('use_case'):
                use_kws = cls.USE_CASE_MAP.get(intent['use_case'], {}).get('keywords', [])
                for ukw in use_kws:
                    if ukw in p_name_lower:
                        score += 20.0

            # Boost for brand match
            if intent.get('brand') and intent['brand'].lower() in p.brand.lower():
                score += 30.0

            # Boost for specific model tokens in query (e.g. "envy", "x360", "legion", "aspire")
            q_tokens = [w for w in query_text.lower().split() if len(w) >= 3 and w not in ['tell', 'about', 'show', 'the', 'what', 'price', 'laptop', 'phone', 'does', 'have', 'with', 'for', 'which', 'product', 'has', 'most', 'best']]
            for qt in q_tokens:
                if qt in p_name_lower:
                    score += 1000.0

            scored_products.append((score, p))

        # Filter candidate list using validate_product_relevance (Strict Budget & Relevance Gate)
        valid_scored = [item for item in scored_products if cls.validate_product_relevance(item[1], intent)]

        # Sort candidate list by computed score DESC or user sort preference
        if intent.get('sort_preference') == 'price_asc':
            valid_scored.sort(key=lambda x: cls.get_normalized_price_inr(x[1]))
        elif intent.get('sort_preference') == 'price_desc':
            valid_scored.sort(key=lambda x: cls.get_normalized_price_inr(x[1]), reverse=True)
        else:
            valid_scored.sort(key=lambda x: x[0], reverse=True)

        final_products = [item[1] for item in valid_scored[:limit]]

        logger.info(f"[AI PIPELINE LOG] Total Candidates: {len(candidates)} | Valid Products Returned: {len(final_products)}")
        for idx, fp in enumerate(final_products, 1):
            fp_norm = cls.get_normalized_price_inr(fp)
            logger.info(f"   {idx}. [ID {fp.id}] {fp.name} | Category: {fp.category.name if fp.category else 'N/A'} | Price: ₹{fp_norm:,.2f} | Rating: {float(fp.rating):.1f}★")
        logger.info("=" * 60)

        return final_products

    # -------------------------------------------------------------------------
    # 4. STRUCTURED CONTEXT BUILDER FOR GEMINI
    # -------------------------------------------------------------------------
    @staticmethod
    def build_structured_context(products):
        """Build clean structured text context from database products for Gemini prompt."""
        if not products:
            return "NO MATCHING PRODUCTS FOUND IN CATALOG DATABASE."

        catalog_entries = []
        for index, p in enumerate(products, 1):
            category_name = p.category.name if p.category else "General"
            specs = json.dumps(p.specifications) if isinstance(p.specifications, dict) else (p.specifications or "N/A")
            norm_p = AIService.get_normalized_price_inr(p)
            catalog_entries.append(
                f"{index}. Product ID: {p.id}\n"
                f"   Name: {p.name}\n"
                f"   Brand: {p.brand}\n"
                f"   Category: {category_name}\n"
                f"   Price: ₹{norm_p:,.2f}\n"
                f"   Rating: {float(p.rating):.1f} / 5.0\n"
                f"   In Stock: {'Yes (' + str(p.stock_quantity) + ' units)' if p.stock_quantity > 0 else 'No'}\n"
                f"   Description: {p.description or 'N/A'}\n"
                f"   Key Specifications: {specs}\n"
            )
        return "\n".join(catalog_entries)

    # -------------------------------------------------------------------------
    # 5. NATURAL RESPONSE GENERATION & GEMINI INTEGRATION
    # -------------------------------------------------------------------------
    @classmethod
    def generate_ai_response(cls, user_query, user_id=None, conversation_history=None):
        """
        Main entry point for AI recommendations:
        1. Extract natural language intent (with conversation history context)
        2. Query MySQL database for matching products via multi-level retrieval
        3. Build structured catalog context
        4. Call Gemini API for response synthesis OR generate natural fallback response
        5. Return clean structured response dictionary
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

        # Handler A: Dataset Statistics Queries
        if q_type == 'dataset_query':
            stat_res = cls.get_dataset_statistics(user_query_clean)
            return {
                'success': True,
                'ai_response': stat_res,
                'recommended_products': [],
                'intent': q_type
            }

        # Handler B: Category Statistics Queries
        if q_type == 'category_query':
            cat_res = cls.get_category_statistics(user_query_clean)
            return {
                'success': True,
                'ai_response': cat_res,
                'recommended_products': [],
                'intent': q_type
            }

        # Handler C: Brand Statistics Queries (when no specific product search requested)
        if q_type == 'brand_query' and not intent.get('product_type') and not intent.get('brand'):
            brand_res = cls.get_brand_statistics(intent, user_query_clean)
            return {
                'success': True,
                'ai_response': brand_res,
                'recommended_products': [],
                'intent': q_type
            }

        # Handler D: General Educational Concept Questions
        if q_type == 'general_question':
            gen_res = cls.generate_general_explanation(user_query_clean)
            return {
                'success': True,
                'ai_response': gen_res,
                'recommended_products': [],
                'intent': q_type
            }

        # Step 2: Retrieve products from MySQL catalog
        products = cls.retrieve_relevant_products(intent, user_query_clean)

        # Handler E: Product Comparison Queries
        if q_type == 'product_comparison' and len(products) >= 2:
            comp_res = cls.generate_product_comparison(products, intent=intent)
            return {
                'success': True,
                'ai_response': comp_res,
                'recommended_products': products[:4],
                'intent': q_type
            }

        # Handler F: Specific Product Detail or Attribute Queries
        if q_type in ['product_detail', 'attribute_query'] and products:
            detail_res = cls.generate_product_detail_response(products[0], user_query_clean)
            return {
                'success': True,
                'ai_response': detail_res,
                'recommended_products': products[:1],
                'intent': q_type
            }

        product_context = cls.build_structured_context(products)

        # Check API key configuration
        api_key = cls.get_api_key()

        # If Gemini API Key is NOT configured, build natural AI response locally using actual DB products
        if not api_key:
            logger.info("GEMINI_API_KEY is not configured. Generating natural response from MySQL products...")
            ai_text = cls._generate_local_natural_response(user_query_clean, intent, products)
            return {
                'success': True,
                'ai_response': ai_text,
                'recommended_products': products,
                'intent': q_type
            }

        # Step 2: Formulate Gemini System Prompt & Context
        system_prompt = (
            "You are the 'AI Shopping Assistant' for an e-commerce platform.\n"
            "Your objective is to provide helpful, polite, and natural shopping recommendations.\n\n"
            "STRICT RULES:\n"
            "1. ONLY recommend products explicitly listed in the DATABASE CATALOG CONTEXT provided below.\n"
            "2. NEVER fabricate or invent product names, prices, specs, ratings, or availability.\n"
            "3. If constraints were relaxed because exact criteria couldn't be met, explain politely and highlight closest alternatives.\n"
            "4. NEVER display internal database category names (like 'Cell Phones & Accessories' or 'category_id') to the user. Use natural English.\n"
            "5. Format product recommendations cleanly with Bullet points, Name, Price (in ₹), Rating, and a brief natural explanation of why it fits their request.\n"
            "6. Always be natural, helpful, and conversational.\n"
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
            f"{product_context}\n"
            f"=======================\n\n"
            f"USER QUESTION: {user_query_clean}\n\n"
            f"ASSISTANT RESPONSE:"
        )

        # Step 3: Call Gemini API with model fallback
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
                    logger.info(f"Model {m_name} failed: {str(ex)}. Trying next model...")

            if not ai_text:
                logger.error(f"Gemini API call failed: {str(last_err)}. Falling back to local natural response.")
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

    @classmethod
    def _generate_local_natural_response(cls, user_query, intent, products):
        """
        Generate natural language AI response without exposing database terms.
        Used when Gemini API Key is absent or as a fast response synthesizer.
        """
        if not products:
            p_type = intent.get('product_type') or "item"
            max_p = intent.get('max_price')
            if max_p:
                return f"I couldn't find a matching **{p_type}** under **₹{max_p:,.0f}** in our catalog database. Would you like to adjust your budget or search for top-rated alternatives?"
            return "I couldn't find a matching product in our current catalog. Try adjusting your budget or asking for a different item."

        intro = ""
        p_type = intent.get('product_type') or "products"
        use_c = intent.get('use_case')
        max_p = intent.get('max_price')

        if intent.get('relaxed_search'):
            intro = f"I couldn't find an exact match matching all strict criteria, but I found these top-rated {p_type} options close to your request:"
        elif use_c and max_p:
            intro = f"Here are great options for **{use_c.replace('_', ' ')}** under **₹{max_p:,.0f}** from our catalog:"
        elif use_c:
            intro = f"Here are top-rated recommendations for **{use_c.replace('_', ' ')}** from our catalog:"
        elif max_p:
            intro = f"Here are the best **{p_type}** options under **₹{max_p:,.0f}**:"
        elif intent.get('min_rating'):
            intro = f"Here are highly rated **{p_type}** options with excellent reviews:"
        else:
            intro = f"Based on your query, here are top recommendations from our catalog:"

        items_summary = []
        for p in products[:5]:
            specs_str = ""
            if isinstance(p.specifications, dict):
                first_few = [f"{k}: {v}" for k, v in list(p.specifications.items())[:2] if isinstance(v, str)]
                if first_few:
                    specs_str = f" ({', '.join(first_few)})"

            norm_price = cls.get_normalized_price_inr(p)
            items_summary.append(
                f"• **{p.name}** ({p.brand}) - **₹{norm_price:,.2f}** | Rating: **{float(p.rating):.1f}★**{specs_str}"
            )

        summary_text = "\n".join(items_summary)
        return f"{intro}\n\n{summary_text}\n\nClick on any product card below to view details or add to your cart!"

