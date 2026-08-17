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
from app.recommendation.parser import RequirementParser

logger = logging.getLogger(__name__)

USD_TO_INR = 83.0


class AIService:
    """
    AI Service Layer - Advanced Natural Language Understanding, Multi-Tier MySQL Product Retrieval Engine,
    Strict Relevance Validation & Disqualification Gate, Gemini API Integration, and Conversational Response Generation.
    Follows MVP Architecture.
    """

    CATEGORY_TAXONOMY = RequirementParser.CATEGORY_TAXONOMY
    ACCESSORY_ROUTING = RequirementParser.ACCESSORY_ROUTING
    COMMON_BRANDS = RequirementParser.COMMON_BRANDS

    _BRANDS_CACHE = None

    @classmethod
    def get_cached_brands(cls):
        """Cache active product brands in memory for instant matching."""
        return RequirementParser.get_cached_brands()

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
        Extract structured shopping intent from user query using RequirementParser.
        """
        req = RequirementParser.extract_requirements(user_query, conversation_history=conversation_history)
        return {
            'product_type': req.get('product_type'),
            'product_intent': req.get('product_intent'),
            'use_case': req.get('use_case'),
            'category_ids': req.get('category_ids', []),
            'category_family': req.get('category_family'),
            'max_price': req.get('max_price'),
            'min_price': req.get('min_price'),
            'brand': req.get('brand'),
            'min_rating': req.get('min_rating'),
            'sort_preference': req.get('sort_preference', 'recommended'),
            'search_terms': req.get('feature_keywords', []),
            'query_type': 'conversation' if req.get('is_conversation') else 'general',
            'is_primary_request': req.get('is_primary_request', True),
            'is_accessory_request': req.get('is_accessory_request', False),
            'target_accessory': req.get('target_accessory'),
            'is_followup': req.get('is_followup', False),
            'is_conversation': req.get('is_conversation', False),
            'conversational_intent': req.get('conversational_intent'),
            'original_query': user_query
        }

    # -------------------------------------------------------------------------
    # 3. SPECIALIZED DATASET EXECUTORS & HELPER METHODS
    # -------------------------------------------------------------------------
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
        """Generate comparison markdown table for products using clean category-aware specifications."""
        if not products:
            return "No products available for comparison."

        from app.services.product_processor import ProductInformationProcessor

        headers = ["Attribute"] + [f"{p.name[:25]}..." for p in products]
        rows = [
            ["Price"] + [f"₹{p.normalized_price_inr:,.2f}" for p in products],
            ["Brand"] + [p.brand for p in products],
            ["Rating"] + [f"{float(p.rating):.1f}★" for p in products],
            ["Category"] + [(p.category.name if p.category else "General") for p in products]
        ]

        # Extract clean specifications for each product
        prod_specs = [p.display_important_specifications if hasattr(p, 'display_important_specifications') else ProductInformationProcessor.extract_important_specifications(p) for p in products]

        # Find common clean specification keys across compared products
        all_keys = []
        for specs in prod_specs:
            for k in specs.keys():
                if k not in all_keys and len(all_keys) < 4:
                    all_keys.append(k)

        for k in all_keys:
            row = [k]
            for specs in prod_specs:
                row.append(specs.get(k, "N/A"))
            rows.append(row)

        table_str = "| " + " | ".join(headers) + " |\n"
        table_str += "| " + " | ".join(["---"] * len(headers)) + " |\n"
        for r in rows:
            table_str += "| " + " | ".join(r) + " |\n"
        return table_str

    @classmethod
    def retrieve_relevant_products(cls, intent, user_query, limit=8):
        """Retrieve relevant products matching intent."""
        from app.recommendation.engine import RecommendationEngine
        rec_res = RecommendationEngine.get_recommendations(user_query=user_query, limit=limit)
        return rec_res.get('products', [])

    # -------------------------------------------------------------------------
    # 4. AI RESPONSE GENERATION & GEMINI INTEGRATION
    # -------------------------------------------------------------------------
    @classmethod
    def generate_ai_response(cls, user_query, user_id=None, conversation_history=None):
        """
        Main entry point for AI recommendations:
        1. Extract intent and handle conversational queries directly.
        2. Leverage Smart Recommendation Engine (RequirementParser, SQLAlchemy Database Filter, RecommendationScorer, Fallback Engine).
        3. Format structured catalog context & explanations.
        4. Call Gemini API for response synthesis OR generate local natural response.
        5. Return response dictionary with recommendations.
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
        
        # Conversational check
        if intent.get('is_conversation'):
            conv_resp = cls._generate_conversational_response(intent.get('conversational_intent', 'greeting'))
            return {
                'success': True,
                'ai_response': conv_resp,
                'recommended_products': [],
                'intent': 'conversation',
                'is_fallback': False
            }

        q_type = intent.get('query_type', 'general')

        # Dataset queries
        if any(term in user_query_clean.lower() for term in ['how many product', 'total product', 'items available', 'catalog size', 'products available']):
            return {
                'success': True,
                'ai_response': cls.get_dataset_statistics(user_query_clean),
                'recommended_products': [],
                'intent': 'dataset_query'
            }

        # Step 2: Use Smart Recommendation Engine
        from app.recommendation.engine import RecommendationEngine
        rec_res = RecommendationEngine.get_recommendations(
            user_query=user_query_clean,
            user_id=user_id,
            conversation_history=conversation_history,
            limit=3
        )

        if rec_res.get('is_conversation'):
            conv_resp = cls._generate_conversational_response(rec_res.get('conversational_intent', 'greeting'))
            return {
                'success': True,
                'ai_response': conv_resp,
                'recommended_products': [],
                'intent': 'conversation',
                'is_fallback': False
            }

        products = rec_res.get('products', [])
        is_fallback = rec_res.get('is_fallback', False)
        fallback_msg = rec_res.get('fallback_message')

        api_key = cls.get_api_key()

        # Local natural AI response synthesis when Gemini API key is absent
        if not api_key:
            ai_text = cls._generate_local_natural_response(user_query_clean, intent, products)
            if is_fallback and fallback_msg and products:
                ai_text = f"💡 **Note**: {fallback_msg}\n\n" + ai_text
            return {
                'success': True,
                'ai_response': ai_text,
                'recommended_products': products,
                'intent': q_type,
                'is_fallback': is_fallback
            }

        # Gemini Prompt Formulation
        catalog_context = cls.build_structured_context(products)
        system_prompt = (
            "You are the AI Shopping Assistant for an e-commerce platform.\n"
            "STRICT CONCISENESS RULES:\n"
            "1. Output ONLY 1 short intro sentence stating what products were found (e.g., 'I found these 3 options for you:').\n"
            "2. Add 1 short follow-up question at the end (e.g., 'Would you like to explore cheaper or higher-rated options?').\n"
            "3. DO NOT write long paragraphs, DO NOT dump raw descriptions, and DO NOT repeat full spec tables in text.\n"
            "4. ONLY recommend products explicitly listed in the catalog context below.\n"
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
            model_names = ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
            ai_text = None

            for m_name in model_names:
                try:
                    model = genai.GenerativeModel(m_name)
                    response = model.generate_content(prompt)
                    if response and hasattr(response, 'text') and response.text:
                        ai_text = response.text.strip()
                        break
                except Exception:
                    pass

            if not ai_text:
                ai_text = cls._generate_local_natural_response(user_query_clean, intent, products)

            if is_fallback and fallback_msg and products:
                ai_text = f"💡 **Note**: {fallback_msg}\n\n" + ai_text

            return {
                'success': True,
                'ai_response': ai_text,
                'recommended_products': products[:3],
                'intent': intent.get('query_type', 'general'),
                'is_fallback': is_fallback
            }

        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}")
            ai_text = cls._generate_local_natural_response(user_query_clean, intent, products)
            if is_fallback and fallback_msg and products:
                ai_text = f"💡 **Note**: {fallback_msg}\n\n" + ai_text
            return {
                'success': True,
                'ai_response': ai_text,
                'recommended_products': products,
                'intent': intent.get('query_type', 'general'),
                'is_fallback': is_fallback
            }

    @staticmethod
    def build_structured_context(products):
        """Build clean summarized text context from database products for Gemini prompt."""
        if not products:
            return "NO MATCHING PRODUCTS FOUND IN CATALOG DATABASE."

        from app.services.product_processor import ProductInformationProcessor

        catalog_entries = []
        for index, p in enumerate(products[:3], 1):
            category_name = p.category.name if (hasattr(p, 'category') and p.category) else "General"
            summary = p.display_short_summary if hasattr(p, 'display_short_summary') else ProductInformationProcessor.generate_short_summary(p)
            features = p.display_key_features if hasattr(p, 'display_key_features') else ProductInformationProcessor.extract_important_features(p, limit=3)
            
            catalog_entries.append(
                f"{index}. Product ID: {p.id}\n"
                f"   Name: {p.name}\n"
                f"   Brand: {p.brand}\n"
                f"   Category: {category_name}\n"
                f"   Price: ₹{p.normalized_price_inr:,.2f}\n"
                f"   Rating: {float(p.rating):.1f} / 5.0\n"
                f"   Short Summary: {summary}\n"
                f"   Key Features: {', '.join(features[:3])}\n"
            )
        return "\n".join(catalog_entries)

    @classmethod
    def _generate_conversational_response(cls, intent):
        """Generate natural conversational response without products."""
        if intent == 'greeting':
            return "Hello! 👋 I'm your AI Shopping Assistant. How can I help you today? You can search for products by category (like Laptops, Mobiles, Headphones, Induction Stoves, Appliances), features, or budget!"
        elif intent == 'help':
            return "I am your AI Shopping Assistant! I can help you search our catalog across all categories, compare products, and find items within your budget."
        elif intent == 'gratitude':
            return "You're very welcome! 😊 Feel free to ask if you need help finding anything else."
        elif intent == 'goodbye':
            return "Goodbye! Have a great day and happy shopping! 👋"
        return "Hello! How can I assist you with your shopping today?"

    @classmethod
    def _generate_local_natural_response(cls, user_query, intent, products):
        """
        Generate concise 1-sentence intro + follow-up question.
        Product cards with 3 key feature bullets are rendered as interactive UI elements.
        """
        if not products:
            return f"Sorry, I couldn't find matching products for '{user_query}' in our catalog. Would you like to explore popular categories like Laptops, Mobiles, Headphones, or Appliances?"

        p_intent = intent.get('product_intent') or intent.get('product_type')
        if p_intent:
            cat_disp = str(p_intent).replace('_', ' ').title()
            return f"Here are the top **{cat_disp}** recommendations matching your request. Would you like to see cheaper or higher-rated options?"
        
        return "I found these top options matching your request. Would you like to filter by budget or higher ratings?"
