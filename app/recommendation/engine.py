import re
import logging
from sqlalchemy import or_, and_, case
from app import db
from app.models.product import Product
from app.models.category import Category
from app.models.recommendation import Recommendation
from app.recommendation.parser import RequirementParser, USD_TO_INR
from app.recommendation.scoring import RecommendationScorer

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Recommendation Engine - Main Smart Recommendation Controller.
    
    Workflow:
    1. Extract requirements via RequirementParser.
    2. Perform database-level filtering using SQLAlchemy queries (limiting memory overhead).
    3. Filter out negative/irrelevant accessory noise via Strict Relevance Gate.
    4. Compute transparent Recommendation Scores (0-100%) and reasons via RecommendationScorer.
    5. Rank candidate items & select Top 5 recommendations.
    6. Execute Fallback Mechanism if 0 exact matches are found (relaxing 1 constraint).
    7. Persist recommendations to MySQL `recommendations` table for logged-in users.
    """

    @classmethod
    def get_recommendations(cls, user_query, user_id=None, conversation_history=None, limit=3):
        """
        Main entry point for generating product recommendations.
        """
        query_text = (user_query or "").strip()
        if not query_text:
            return {
                'success': False,
                'requirements': {},
                'products': [],
                'is_fallback': False,
                'fallback_message': None,
                'user_message': query_text
            }

        # Step 1: Parse requirements
        reqs = RequirementParser.extract_requirements(query_text, conversation_history=conversation_history)

        # Conversational intent handling (e.g., greetings, help, thanks, bye)
        if reqs.get('is_conversation'):
            return {
                'success': True,
                'requirements': reqs,
                'products': [],
                'is_fallback': False,
                'fallback_message': None,
                'user_message': query_text,
                'is_conversation': True,
                'conversational_intent': reqs.get('conversational_intent')
            }

        # Determine limit (3 by default, or requested limit 5 if specified)
        actual_limit = reqs.get('requested_limit', limit)

        # Step 2 & 3: Database Candidate Retrieval & Validation
        candidates, is_fallback, fallback_msg = cls._retrieve_and_validate_candidates(reqs, limit=60)

        # Step 4 & 5: Recommendation Scoring & Explanation Generation
        scored_products = []
        for p in candidates:
            score, reason = RecommendationScorer.score_product(p, reqs)
            if score > 0.0:
                p.recommendation_score = score
                p.recommendation_reason = reason
                scored_products.append((score, p))

        # Step 6: Ranking & Top Limit Selection
        if reqs.get('sort_preference') == 'price_asc':
            scored_products.sort(key=lambda x: float(x[1].normalized_price_inr))
        elif reqs.get('sort_preference') == 'price_desc':
            scored_products.sort(key=lambda x: float(x[1].normalized_price_inr), reverse=True)
        elif reqs.get('sort_preference') == 'rating':
            scored_products.sort(key=lambda x: float(x[1].rating or 0.0), reverse=True)
        else:
            scored_products.sort(key=lambda x: x[0], reverse=True)

        top_products = [item[1] for item in scored_products[:actual_limit]]

        # If zero candidates pass relevance scoring, return empty list with clear message (NO UNRELATED PRODUCTS)
        if not top_products:
            is_fallback = True
            fallback_msg = "Sorry, I couldn't find a matching product in our catalog."

        # Step 7: DB Persistence for Authenticated Users
        if user_id and top_products:
            cls._persist_recommendations(user_id, top_products)

        return {
            'success': True,
            'requirements': reqs,
            'products': top_products,
            'is_fallback': is_fallback,
            'fallback_message': fallback_msg,
            'user_message': query_text
        }

    @classmethod
    def _retrieve_and_validate_candidates(cls, reqs, limit=60):
        """
        Perform SQL queries & apply strict relevance filters.
        Executes constraint relaxation fallback if 0 candidates match.
        """
        norm_price_expr = case(
            (and_(Product.category_id > 4, Product.price < 3000.0), Product.price * USD_TO_INR),
            else_=Product.price
        )

        base_query = Product.query.filter(Product.is_active == True, Product.is_available == True)

        # Build candidate filters based on requirements
        candidates = cls._execute_sql_query(base_query, norm_price_expr, reqs, limit=limit)
        valid_candidates = cls._filter_valid_products(candidates, reqs)

        is_fallback = False
        fallback_msg = None

        # FALLBACK MECHANISM: Progressively relax price/rating constraints ONLY if 0 exact matches found
        if not valid_candidates:
            relaxed_reqs = dict(reqs)

            # Relax budget and rating limits while preserving product_type/title filters
            if relaxed_reqs.get('max_price') is not None or relaxed_reqs.get('min_rating') is not None:
                relaxed_reqs['max_price'] = None
                relaxed_reqs['min_price'] = None
                relaxed_reqs['min_rating'] = None

                fallback_candidates = cls._execute_sql_query(base_query, norm_price_expr, relaxed_reqs, limit=limit)
                valid_candidates = cls._filter_valid_products(fallback_candidates, relaxed_reqs)

            if valid_candidates:
                is_fallback = True
                fallback_msg = "No exact match found within initial price/rating filter. Showing top closest options from catalog."
            else:
                is_fallback = True
                fallback_msg = "Sorry, I couldn't find a matching product in our catalog."

        return valid_candidates, is_fallback, fallback_msg

    @classmethod
    def _execute_sql_query(cls, base_query, norm_price_expr, reqs, limit=60):
        """Execute parameterized SQLAlchemy filter queries with primary category prioritization."""
        q = base_query

        # Price Filter
        if reqs.get('max_price') is not None:
            q = q.filter(norm_price_expr <= float(reqs['max_price']))
        if reqs.get('min_price') is not None:
            q = q.filter(norm_price_expr >= float(reqs['min_price']))

        # Rating Filter
        if reqs.get('min_rating') is not None:
            q = q.filter(Product.rating >= reqs['min_rating'])

        # Brand Filter
        if reqs.get('brand'):
            q = q.filter(Product.brand.ilike(f"%{reqs['brand']}%"))

        cat_ids = reqs.get('category_ids', [])
        keywords = reqs.get('feature_keywords', [])
        p_type = reqs.get('product_type')
        is_acc = reqs.get('is_accessory_request', False)
        target_acc = reqs.get('target_accessory')

        title_terms = list(keywords)
        p_intent = reqs.get('product_intent') or p_type
        if p_intent and p_intent in RequirementParser.CATEGORY_TAXONOMY:
            title_terms.extend(RequirementParser.CATEGORY_TAXONOMY[p_intent]['primary_terms'][:8])

        if is_acc and target_acc in RequirementParser.ACCESSORY_ROUTING:
            routing = RequirementParser.ACCESSORY_ROUTING[target_acc]
            title_terms = routing['target_terms']
            cat_ids = routing['cat_ids']

        title_clauses = []
        for term in title_terms:
            if len(term) >= 2:
                title_clauses.append(Product.name.ilike(f"%{term}%"))

        candidates = []

        # TIER 1: Search Primary Category first (e.g. Cat 2 for mobile, Cat 1 for laptop, Cat 3 for headphones, Cat 4 for watch, Cat 38 for toys, Cat 35 for sports)
        primary_cat = cat_ids[0] if cat_ids else None
        if primary_cat and title_clauses:
            candidates = q.filter(and_(Product.category_id == primary_cat, or_(*title_clauses)))\
                .order_by(Product.rating.desc()).limit(limit).all()
            if not candidates:
                candidates = q.filter(Product.category_id == primary_cat)\
                    .order_by(Product.rating.desc()).limit(limit).all()
        elif primary_cat:
            candidates = q.filter(Product.category_id == primary_cat)\
                .order_by(Product.rating.desc()).limit(limit).all()

        # TIER 2: Search across all secondary allowed cat_ids
        if not candidates and len(cat_ids) > 1:
            if title_clauses:
                candidates = q.filter(and_(Product.category_id.in_(cat_ids), or_(*title_clauses)))\
                    .order_by(Product.rating.desc()).limit(limit).all()
            if not candidates:
                candidates = q.filter(Product.category_id.in_(cat_ids))\
                    .order_by(Product.rating.desc()).limit(limit).all()

        # TIER 3: Title Search across all categories if no category was specified
        if not candidates and not cat_ids and title_clauses:
            candidates = q.filter(or_(*title_clauses)).order_by(Product.rating.desc()).limit(limit).all()

        logger.info(f"[AI DEBUG LOG] Query: '{reqs.get('original_query')}' | Intent: {p_intent} | Cats: {cat_ids} | Keywords: {keywords} | SQL Candidates Retained: {len(candidates)}")
        return candidates

    @classmethod
    def _filter_valid_products(cls, candidates, reqs):
        """Strict relevance validation gate filtering out noise and non-matching accessories."""
        valid = []
        p_intent = reqs.get('product_intent') or reqs.get('product_type')
        cat_family = reqs.get('category_family')
        is_acc = reqs.get('is_accessory_request', False)
        target_acc = reqs.get('target_accessory')
        max_p = reqs.get('max_price')
        min_p = reqs.get('min_price')
        req_cat_ids = reqs.get('category_ids', [])

        for p in candidates:
            norm_price = float(p.normalized_price_inr)
            p_name_lower = p.name.lower()
            cat_id = p.category_id

            # Budget check
            if max_p is not None and norm_price > max_p:
                continue
            if min_p is not None and norm_price < min_p:
                continue

            # Accessory check
            if is_acc and target_acc:
                if 'mouse' in target_acc:
                    if not ('mouse' in p_name_lower or 'mice' in p_name_lower):
                        continue
                    if 'mouse pad' in p_name_lower or 'mousepad' in p_name_lower:
                        continue
                elif 'bag' in target_acc:
                    if not (('laptop' in p_name_lower or 'computer' in p_name_lower or 'macbook' in p_name_lower) and
                            ('bag' in p_name_lower or 'backpack' in p_name_lower or 'sleeve' in p_name_lower or 'case' in p_name_lower)):
                        continue
                elif 'tripod' in target_acc:
                    if not ('tripod' in p_name_lower or 'monopod' in p_name_lower):
                        continue
                elif 'case' in target_acc:
                    if not (('phone' in p_name_lower or 'iphone' in p_name_lower or 'galaxy' in p_name_lower) and
                            ('case' in p_name_lower or 'cover' in p_name_lower)):
                        continue
                valid.append(p)
                continue

            # If user explicitly targeted specific categories and candidate is from an unrelated category
            if req_cat_ids and cat_id not in req_cat_ids:
                continue

            # Strict Product Intent & Category Family Gating
            if p_intent and not is_acc:
                # Disqualify earphones/headphones if user explicitly asked for non-audio product
                if p_intent not in ['headphone', 'audio', 'musical_instruments']:
                    if re.search(r'\b(headphone|headphones|earphone|earphones|earbud|earbuds|airpods|headset)s?\b', p_name_lower):
                        continue

                # Beauty / Cosmetics Gating
                if cat_family == 'beauty' or p_intent in ['beauty', 'makeup', 'cosmetics', 'lipstick', 'skincare', 'haircare']:
                    if any(bad in p_name_lower for bad in ['refrigerator', 'mini fridge', 'stove', 'cooktop', 'microwave', 'oven', 'vanity table', 'bed frame', 'screwdriver', 'flag', 'volleyball', 'vacuum', 'dishwasher', 'laptop', 'headphone', 'phone', 'tumbler', 'coffee mug', 'straw cup', 'teacher gift']):
                        continue

                # Specific Product Type Extra Gates
                tax_info = RequirementParser.CATEGORY_TAXONOMY.get(p_intent)
                if tax_info:
                    dis_accs = tax_info.get('disqualifying_accessories', [])
                    if any(re.search(r'\b' + re.escape(dis) + r'\b', p_name_lower) for dis in dis_accs):
                        continue

                if p_intent == 'mobile':
                    if cat_id not in [2, 17]:
                        continue
                    if any(bad in p_name_lower for bad in ['case', 'cover', 'protector', 'tempered glass', 'charger', 'cable', 'mount', 'lanyard', 'holster', 'armband', 'ring holder', 'selfie stick', 'skin', 'replacement', 'stylus', 'grip', 'bracket', 'pouch', 'watch', 'smart watch', 'earphone', 'headphone', 'headset', 'compatible', 'film', 'glass', 'lens protector']):
                        continue

                elif p_intent == 'laptop':
                    if any(bad in p_name_lower for bad in ['motherboard', 'bag', 'backpack', 'sleeve', 'case', 'skin', 'stand', 'holder', 'charger', 'adapter', 'cable', 'protector', 'keyboard cover', 'docking station', 'cooling pad', 'ram', 'memory module', 'screen replacement', 'battery', 'decal', 'mouse pad', 'mousepad', 'mouse', 'keyboard', 'board']):
                        continue

                elif p_intent == 'watch':
                    if any(bad in p_name_lower for bad in ['watch band', 'watch strap', 'watchband', 'bezel', 'screen protector', 'watch charger', 'charging cable', 'watch case', 'watch stand', 'watch winder']):
                        continue

                elif p_intent == 'cooktop':
                    if any(bad in p_name_lower for bad in ['knob', 'mat', 'pad', 'cord', 'organizer', 'rack', 'holder', 'stand', 'spatula', 'spoon', 'towel', 'cleaner']):
                        continue

                elif p_intent == 'washing_machine':
                    if any(bad in p_name_lower for bad in ['hose', 'pipe', 'cover', 'inlet', 'drain', 'vibration pad', 'foot pad', 'door lock', 'lint filter', 'cleaner', 'tablet']):
                        continue

                elif p_intent == 'mixer_grinder':
                    if any(bad in p_name_lower for bad in ['blade', 'lid', 'gasket', 'ring', 'pestle', 'nail grinder', 'pet grinder', 'mat', 'organizer']):
                        continue

                elif p_intent == 'toys_games':
                    if any(bad in p_name_lower for bad in ['dewalt', 'battery adapter', 'power wheels adapter', 'catnip', 'chew toy', 'hamster', 'screen protector']):
                        continue

                elif p_intent == 'pet_supplies':
                    if any(bad in p_name_lower for bad in ['condiment container', 'faucet splash', 'sink splash', 'power wheels']):
                        continue

                elif reqs.get('use_case') == 'running' or p_intent == 'shoe':
                    if any(bad in p_name_lower for bad in ['necklace', 'pendant', 'ring', 'jewelry', 'socks', 'lace', 'sandal', 'slipper', 'heel', 'cosplay', 'shirt', 'pant']):
                        continue

            valid.append(p)

        return valid

    @classmethod
    def _persist_recommendations(cls, user_id, top_products):
        """Save top recommendations to MySQL `recommendations` table."""
        try:
            for p in top_products:
                score = getattr(p, 'recommendation_score', 85.0)
                reason = getattr(p, 'recommendation_reason', 'Smart AI Recommendation')
                rec_entry = Recommendation(
                    user_id=user_id,
                    product_id=p.id,
                    recommendation_score=min(99.99, max(0.00, score)),
                    reason=reason[:250]
                )
                db.session.add(rec_entry)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to persist recommendations for user {user_id}: {str(e)}")
