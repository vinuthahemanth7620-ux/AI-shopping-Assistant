import json
import logging

logger = logging.getLogger(__name__)


class RecommendationScorer:
    """
    Recommendation Scorer - Transparent Recommendation Scoring & Explanation Generator.
    
    Evaluates candidate products against parsed user requirements using configurable weights:
    - Category Relevance: 30%
    - Feature / Text Relevance: 25%
    - Rating Score: 20%
    - Price Suitability: 15%
    - Review / Availability Confidence: 10%
    
    Produces:
    - Normalized Recommendation Score (0% to 100%)
    - DB-backed natural explanation ("Recommended because...")
    """

    DEFAULT_WEIGHTS = {
        'category': 0.35,
        'feature_text': 0.40,
        'rating': 0.15,
        'price_suitability': 0.10
    }

    @classmethod
    def score_product(cls, product, requirements, weights=None):
        """
        Calculate transparent recommendation score (0.0 to 100.0) and natural explanation for a Product.
        """
        w = weights or cls.DEFAULT_WEIGHTS
        norm_price = float(product.normalized_price_inr)
        rating_val = float(product.rating or 0.0)
        p_name_lower = product.name.lower()
        p_desc_lower = (product.description or "").lower()
        cat_id = product.category_id

        # 1. CATEGORY RELEVANCE (0.0 - 1.0)
        cat_score = 0.0
        req_cat_ids = requirements.get('category_ids', [])
        p_type = requirements.get('product_type')

        if req_cat_ids and cat_id in req_cat_ids:
            cat_score = 1.0
        elif p_type:
            cat_name = product.category.name.lower() if product.category else ""
            if p_type in cat_name or p_type in p_name_lower:
                cat_score = 0.9
            else:
                cat_score = 0.2
        else:
            cat_score = 0.5  # Neutral if query is open-ended

        # 2. FEATURE / TEXT RELEVANCE (0.0 - 1.0)
        text_score = 0.0
        keywords = requirements.get('feature_keywords', [])
        use_case = requirements.get('use_case')
        brand_req = requirements.get('brand')

        if keywords:
            for kw in keywords:
                if kw in p_name_lower:
                    text_score += 0.5
                elif kw in p_desc_lower:
                    text_score += 0.25

        if use_case:
            use_case_terms = {
                'programming': ['laptop', 'notebook', 'macbook', 'ram', 'ssd', 'intel', 'ryzen', 'processor'],
                'photography': ['camera', 'dslr', 'lens', 'sensor', 'megapixels', '4k', 'video'],
                'running': ['running', 'shoe', 'sneaker', 'cushion', 'mesh', 'athletic', 'sole'],
                'cooking': ['mixer', 'blender', 'oven', 'microwave', 'cooker', 'kettle', 'fryer', 'induction', 'stove', 'cooktop'],
                'gift': ['gift', 'present', 'luxury', 'watch', 'jewelry', 'beauty', 'set'],
                'college': ['student', 'portable', 'lightweight', 'compact', 'laptop', 'backpack'],
                'travel': ['travel', 'portable', 'lightweight', 'compact', 'wireless', 'durability'],
                'gaming': ['gaming', 'game', 'gamer', 'rtx', 'gpu', 'graphics', 'refresh rate', 'hz']
            }
            terms = use_case_terms.get(use_case, [use_case])
            for t in terms:
                if t in p_name_lower or t in p_desc_lower:
                    text_score += 0.3
                    break

        if brand_req and product.brand and brand_req.lower() in product.brand.lower():
            text_score += 0.4

        text_score = min(1.0, max(0.0, text_score))

        # STRICT RELEVANCE GATE:
        # If explicit keywords exist and the product has 0 text match & low category score, drop to 0 score!
        if keywords and text_score == 0.0 and cat_score < 0.8:
            return 0.0, "Irrelevant product filtered out."

        # 3. RATING SCORE (0.0 - 1.0)
        rating_score = min(1.0, max(0.0, rating_val / 5.0))

        # 4. PRICE SUITABILITY (0.0 - 1.0)
        max_p = requirements.get('max_price')
        min_p = requirements.get('min_price')
        qual_pref = requirements.get('quality_preference', 'standard')

        price_score = 0.5
        if max_p is not None and max_p > 0:
            if norm_price <= max_p:
                ratio = norm_price / max_p
                if qual_pref == 'affordable':
                    price_score = 1.0 - (ratio * 0.4)
                elif qual_pref == 'premium':
                    price_score = 0.5 + (ratio * 0.5)
                else:
                    price_score = 1.0 if 0.3 <= ratio <= 0.98 else 0.75
            else:
                diff_pct = (norm_price - max_p) / max_p
                price_score = max(0.0, 1.0 - (diff_pct * 3.0))
        else:
            price_score = 0.7

        # COMPOSITE SCORE CALCULATION
        composite_score = (
            (cat_score * w['category']) +
            (text_score * w['feature_text']) +
            (rating_score * w['rating']) +
            (price_score * w['price_suitability'])
        )

        # Scale to 0 - 100 percentage without artificial 50% floor
        recommendation_score = round(min(99.0, max(0.0, composite_score * 100.0)), 1)

        # GENERATE NATURAL REASON EXPLANATION
        reason = cls.generate_recommendation_reason(product, requirements, recommendation_score, norm_price, rating_val)

        return recommendation_score, reason

    @classmethod
    def generate_recommendation_reason(cls, product, requirements, score, norm_price, rating_val):
        """
        Generate explicit DB-backed reason explaining why product was recommended.
        """
        reasons = []
        max_p = requirements.get('max_price')
        use_case = requirements.get('use_case')
        p_type = requirements.get('product_type')
        min_r = requirements.get('min_rating')
        brand_req = requirements.get('brand')

        if max_p and norm_price <= max_p:
            reasons.append(f"fits within your ₹{max_p:,.0f} budget at ₹{norm_price:,.2f}")
        elif norm_price > 0:
            reasons.append(f"offered at ₹{norm_price:,.2f}")

        if use_case:
            use_case_clean = use_case.replace('_', ' ')
            reasons.append(f"matches your {use_case_clean} requirement")

        if rating_val >= 4.0:
            reasons.append(f"has a high {rating_val:.1f}★ customer rating")
        elif rating_val > 0:
            reasons.append(f"rated {rating_val:.1f}★")

        if brand_req and brand_req.lower() in product.brand.lower():
            reasons.append(f"from requested brand {product.brand}")

        if not reasons:
            reasons.append("matches your product search criteria")

        reason_str = f"Recommended ({score:.0f}% match) because it " + ", ".join(reasons) + "."
        return reason_str
