import os
import re
import json
import logging
import google.generativeai as genai
from flask import current_app
from sqlalchemy import or_, func
from app import db
from app.models.product import Product
from app.models.category import Category

logger = logging.getLogger(__name__)

class AIService:
    """
    AI Service Layer - Handles natural language understanding, database product context retrieval,
    Gemini API prompt engineering, multi-turn context, and response generation.
    Strictly follows MVP architecture.
    """

    @staticmethod
    def get_api_key():
        """Retrieve Gemini API key safely from Flask config or environment variables."""
        try:
            key = current_app.config.get('GEMINI_API_KEY') if current_app else os.getenv('GEMINI_API_KEY')
            return key.strip() if key else ''
        except Exception as e:
            logger.error(f"Error fetching GEMINI_API_KEY: {str(e)}")
            return ''

    @classmethod
    def extract_user_intent(cls, user_query):
        """
        Analyze user text query to extract shopping parameters:
        - category_id / category_name
        - max_price / budget
        - min_price
        - brand
        - min_rating
        - keywords / feature search terms
        - query_type ('budget', 'category', 'brand', 'rating', 'comparison', 'general')
        """
        query_text = user_query.strip().lower()
        intent = {
            'category_id': None,
            'category_name': None,
            'max_price': None,
            'min_price': None,
            'brand': None,
            'min_rating': None,
            'keywords': [],
            'query_type': 'general'
        }

        # 1. Detect Category
        categories = Category.query.filter_by(is_active=True).all()
        for cat in categories:
            cat_name = cat.name.lower()
            cat_singular = cat_name[:-1] if cat_name.endswith('s') else cat_name
            if cat_name in query_text or cat_singular in query_text:
                intent['category_id'] = cat.id
                intent['category_name'] = cat.name
                intent['query_type'] = 'category'
                break

        # Additional category keyword synonyms
        if not intent['category_id']:
            synonyms = {
                'laptop': 'Laptops', 'notebook': 'Laptops', 'macbook': 'Laptops',
                'mobile': 'Mobiles', 'phone': 'Mobiles', 'smartphone': 'Mobiles', 'iphone': 'Mobiles',
                'headphone': 'Headphones', 'earphone': 'Headphones', 'earbud': 'Headphones', 'headset': 'Headphones',
                'watch': 'Smart Watches', 'smartwatch': 'Smart Watches'
            }
            for syn, target_cat in synonyms.items():
                if syn in query_text:
                    found_cat = Category.query.filter(Category.name.ilike(f"%{target_cat}%")).first()
                    if found_cat:
                        intent['category_id'] = found_cat.id
                        intent['category_name'] = found_cat.name
                        intent['query_type'] = 'category'
                        break

        # 2. Detect Price / Budget (e.g., "under 60000", "below ₹5000", "less than 70k", "budget of 30000")
        price_patterns = [
            r'(?:under|below|less than|within|max|up to|budget of|under\s*₹?|below\s*₹?)\s*₹?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(k|thousand|lakh)?',
            r'₹\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(k|thousand|lakh)?',
            r'(\d+)\s*(?:k|thousand)\s*(?:rupees|rs|inr)?'
        ]

        for pattern in price_patterns:
            match = re.search(pattern, query_text)
            if match:
                raw_val = match.group(1).replace(',', '')
                multiplier = match.group(2) if len(match.groups()) > 1 else None
                try:
                    val = float(raw_val)
                    if multiplier in ['k', 'thousand']:
                        val *= 1000
                    elif multiplier == 'lakh':
                        val *= 100000
                    intent['max_price'] = val
                    intent['query_type'] = 'budget'
                    break
                except ValueError:
                    pass

        # 3. Detect Brand
        distinct_brands = db.session.query(Product.brand).filter(Product.is_active == True).distinct().all()
        for b_row in distinct_brands:
            b_name = b_row[0]
            if b_name and b_name.lower() in query_text:
                intent['brand'] = b_name
                intent['query_type'] = 'brand'
                break

        # 4. Detect Rating filter (e.g. "best rated", "highest rating", "top rated", "4 star", "5 star")
        if any(term in query_text for term in ['best rated', 'highest rating', 'top rated', 'high rating', 'most rated', 'best rating']):
            intent['min_rating'] = 4.0
            intent['query_type'] = 'rating'
        elif re.search(r'(\d(?:\.\d)?)\s*(?:star|\+?\s*rating)', query_text):
            r_match = re.search(r'(\d(?:\.\d)?)\s*(?:star|\+?\s*rating)', query_text)
            try:
                r_val = float(r_match.group(1))
                if 0.0 <= r_val <= 5.0:
                    intent['min_rating'] = r_val
                    intent['query_type'] = 'rating'
            except ValueError:
                pass

        # 5. Extract Feature Keywords (photography, gaming, battery, student, programming, noise cancel)
        feature_words = ['photography', 'camera', 'gaming', 'battery', 'student', 'programming', 'code', 'noise', 'wireless', 'display', 'screen']
        for fw in feature_words:
            if fw in query_text:
                intent['keywords'].append(fw)

        return intent

    @classmethod
    def retrieve_relevant_products(cls, intent, user_query, limit=8):
        """
        Query MySQL database using SQLAlchemy ORM based on extracted intent and user query.
        Returns list of matching Product model instances.
        """
        query = Product.query.filter(Product.is_active == True, Product.is_available == True)

        # Apply Category Filter
        if intent.get('category_id'):
            query = query.filter(Product.category_id == intent['category_id'])

        # Apply Price Filter
        if intent.get('max_price') is not None:
            query = query.filter(Product.price <= intent['max_price'])

        if intent.get('min_price') is not None:
            query = query.filter(Product.price >= intent['min_price'])

        # Apply Brand Filter
        if intent.get('brand'):
            query = query.filter(Product.brand == intent['brand'])

        # Apply Rating Filter
        if intent.get('min_rating') is not None:
            query = query.filter(Product.rating >= intent['min_rating'])

        # Apply Feature Keywords or Search Terms
        keywords = intent.get('keywords', [])
        if keywords:
            or_conditions = []
            for kw in keywords:
                term = f"%{kw}%"
                or_conditions.append(Product.name.ilike(term))
                or_conditions.append(Product.description.ilike(term))
            # Try to filter by keyword if present
            kw_filtered = query.filter(or_(*or_conditions))
            if kw_filtered.count() > 0:
                query = kw_filtered

        # Ordering strategy based on intent
        if intent.get('query_type') == 'rating' or intent.get('min_rating'):
            query = query.order_by(Product.rating.desc(), Product.price.asc())
        elif intent.get('max_price'):
            query = query.order_by(Product.price.desc(), Product.rating.desc())
        else:
            query = query.order_by(Product.rating.desc(), Product.id.desc())

        products = query.limit(limit).all()

        # Fallback 1: If general query with no specific category/brand/price filter, return top rated catalog products
        if not products and not intent.get('category_id') and not intent.get('max_price') and not intent.get('brand'):
            products = Product.query.filter(Product.is_active == True, Product.is_available == True)\
                .order_by(Product.rating.desc()).limit(6).all()

        return products

    @staticmethod
    def build_structured_context(products):
        """Build clean structured text context from database products for Gemini prompt."""
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
                f"   Price: ₹{float(p.price):,.2f}\n"
                f"   Rating: {float(p.rating):.1f} / 5.0\n"
                f"   In Stock: {'Yes (' + str(p.stock_quantity) + ' units)' if p.stock_quantity > 0 else 'No'}\n"
                f"   Description: {p.description or 'N/A'}\n"
                f"   Key Specifications: {specs}\n"
            )
        return "\n".join(catalog_entries)

    @classmethod
    def generate_ai_response(cls, user_query, user_id=None, conversation_history=None):
        """
        Main entry point for AI recommendations:
        1. Parse query intent
        2. Query MySQL database for matching products
        3. Formulate Gemini system prompt & context
        4. Call Gemini API or fallback
        5. Return clean structured response
        """
        user_query_clean = user_query.strip()
        if not user_query_clean:
            return {
                'success': False,
                'ai_response': "Please provide a valid question about products or shopping.",
                'recommended_products': [],
                'intent': 'empty'
            }

        # Step 1: Extract intent & Retrieve database products
        intent = cls.extract_user_intent(user_query_clean)
        products = cls.retrieve_relevant_products(intent, user_query_clean)
        product_context = cls.build_structured_context(products)

        # Check API key configuration
        api_key = cls.get_api_key()
        if not api_key:
            logger.warning("GEMINI_API_KEY is missing or empty.")
            if products:
                prod_names = ", ".join([f"**{p.name}** (₹{float(p.price):,.2f})" for p in products[:3]])
                fallback_msg = (
                    "⚠️ *Note: Gemini API Key is not configured in environment variables.*\n\n"
                    f"However, based on your search in our catalog database, here are matching products:\n"
                    f"{prod_names}.\n\n"
                    "Please configure `GEMINI_API_KEY` in `.env` to enable full AI conversational responses."
                )
            else:
                fallback_msg = (
                    "I couldn't find a matching product in our current catalog for your request. "
                    "Try increasing your budget or choosing another category."
                )
            return {
                'success': True,
                'ai_response': fallback_msg,
                'recommended_products': products,
                'intent': intent.get('query_type', 'general')
            }

        # Step 2: Formulate System Prompt
        system_prompt = (
            "You are the 'AI Shopping Assistant' for an e-commerce platform.\n"
            "Your objective is to provide helpful, polite, and accurate shopping recommendations.\n\n"
            "STRICT RULES:\n"
            "1. ONLY recommend products explicitly listed in the DATABASE CATALOG CONTEXT provided below.\n"
            "2. NEVER fabricate or invent product names, prices, specs, ratings, or availability.\n"
            "3. If the DATABASE CATALOG CONTEXT says 'NO MATCHING PRODUCTS FOUND IN CATALOG DATABASE', state clearly: "
            "'I couldn't find a matching product in our current catalog. Try increasing your budget or choosing another category.'\n"
            "4. If asked about non-shopping topics (e.g. weather, politics, general coding, history), politely remind the user "
            "that you are an AI Shopping Assistant designed specifically to help find and compare products in our catalog.\n"
            "5. Format product recommendations cleanly with Bullet points, Name, Price (in ₹), Rating, and a brief explanation of why it suits the request.\n"
            "6. Always respect the user's budget and criteria.\n"
        )

        # Include past conversation context if provided
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
                logger.error(f"Gemini API generation failed for all models: {str(last_err)}")
                if products:
                    prod_summary = "\n".join([f"• **{p.name}** ({p.brand}) - ₹{float(p.price):,.2f} | Rating: {float(p.rating):.1f}★" for p in products])
                    ai_text = (
                        "Here are matching recommendations from our database:\n\n"
                        f"{prod_summary}\n\n"
                        "*(Note: AI synthesis experienced a temporary delay, but product details above are accurate).* "
                    )
                else:
                    ai_text = "I couldn't find a matching product in our current catalog. Try increasing your budget or choosing another category."

            return {
                'success': True,
                'ai_response': ai_text,
                'recommended_products': products,
                'intent': intent.get('query_type', 'general')
            }

        except Exception as e:
            logger.error(f"Error in Gemini API call: {str(e)}")
            return {
                'success': False,
                'ai_response': "An unexpected error occurred while processing your shopping request. Please try again.",
                'recommended_products': products if products else [],
                'intent': intent.get('query_type', 'error')
            }
