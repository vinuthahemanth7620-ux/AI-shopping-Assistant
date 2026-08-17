import os
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath('.'))

from app import create_app
from app.recommendation.engine import RecommendationEngine


def run_ai_retrieval_tests():
    app = create_app()
    app.config['TESTING'] = True

    print("=" * 80)
    print("AI SHOPPING ASSISTANT — RETRIEVAL SYSTEM & RELEVANCE EVALUATION")
    print("=" * 80)

    test_queries = [
        ("I need an induction stove", ["induction", "stove", "cooktop", "cooker", "appliance", "grill"]),
        ("Show me induction cooktops", ["induction", "cooktop", "stove", "burner", "appliance"]),
        ("I want a laptop", ["laptop", "notebook", "macbook", "chromebook", "ultrabook", "computer"]),
        ("Suggest a gaming laptop", ["laptop", "gaming", "rtx", "legion", "notebook", "zephyrus"]),
        ("Laptop under 60000", ["laptop", "notebook", "macbook", "ultrabook", "computer"]),
        ("I need wireless headphones", ["headphone", "headphones", "earbud", "earbuds", "airpods", "headset", "audio"]),
        ("Show me smartphones", ["phone", "smartphone", "iphone", "galaxy", "pixel", "mobile", "android"]),
        ("I want a washing machine", ["washing", "washer", "dryer", "machine", "laundry"]),
        ("Suggest a microwave oven", ["microwave", "oven", "air fryer", "fryer", "toaster"]),
        ("I need a mixer grinder", ["mixer", "grinder", "blender", "juicer", "processor"]),
        ("Show me running shoes", ["running", "shoe", "shoes", "sneaker", "footwear", "saucony", "brooks"]),
        ("I want a smartwatch", ["smartwatch", "watch", "garmin", "apple watch", "galaxy watch"]),
        ("Suggest a digital camera", ["camera", "dslr", "digital", "mirrorless", "sony", "vlogging"]),
        ("I need a comfortable office chair", ["chair", "office", "executive", "ergonomic", "desk", "seat"]),
        ("Show me kitchen appliances", ["mixer", "blender", "stove", "cooktop", "microwave", "appliance", "cooker"]),
        ("Find products under 5000", ["laptop", "phone", "shoe", "watch", "camera", "headphone", "item"]),
        ("Show me highly rated headphones", ["headphone", "headphones", "earbud", "earbuds", "airpods", "bose", "sony"]),
        ("I need a phone with good reviews", ["phone", "smartphone", "iphone", "galaxy", "pixel", "mobile"]),
        ("Find something for cooking without gas", ["induction", "cooktop", "stove", "cooker", "appliance", "electric"]),
        ("Show me something useful for my kitchen", ["cooktop", "stove", "mixer", "blender", "microwave", "appliance", "kitchen"])
    ]

    total_relevant = 0
    total_returned = 0

    with app.app_context():
        for idx, (query, target_terms) in enumerate(test_queries, 1):
            res = RecommendationEngine.get_recommendations(query, limit=5)
            products = res.get('products', [])
            is_fallback = res.get('is_fallback', False)
            fallback_msg = res.get('fallback_message')

            query_returned = len(products)
            query_relevant = 0

            print(f"\nQUERY {idx:02d}: '{query}'")
            print(f"  * Status: {'Fallback/Clarification' if is_fallback else 'Success'}")
            if fallback_msg:
                print(f"  * Clarification: {fallback_msg[:90]}...")

            for p in products:
                p_name_lower = p.name.lower()
                p_desc_lower = (p.description or "").lower()
                cat_name_lower = p.category.name.lower() if p.category else ""

                # Relevance check: product name, description, or category name contains any target term
                is_rel = any(term in p_name_lower or term in p_desc_lower or term in cat_name_lower for term in target_terms)
                
                # Zero AirPods noise check for non-headphone queries
                if "headphone" not in target_terms and "earbud" not in target_terms and "airpods" not in target_terms:
                    if any(audio_bad in p_name_lower for audio_bad in ["airpods", "earbuds", "earphone"]):
                        is_rel = False

                if is_rel:
                    query_relevant += 1

                price_inr = float(p.normalized_price_inr)
                print(f"    - [{p.id}] {p.name[:50]} | ₹{price_inr:,.0f} | Rating: {p.rating}★ | Score: {p.recommendation_score}% | Rel: {'✅' if is_rel else '❌'}")

            total_returned += query_returned
            total_relevant += query_relevant

            rel_pct = (query_relevant / query_returned * 100.0) if query_returned > 0 else (100.0 if is_fallback else 0.0)
            print(f"  * Query Relevance: {rel_pct:.1f}% ({query_relevant}/{query_returned} relevant items)")

        overall_rel_pct = (total_relevant / total_returned * 100.0) if total_returned > 0 else 0.0
        print("\n" + "=" * 80)
        print("RELEVANCE EVALUATION METRICS SUMMARY")
        print("=" * 80)
        print(f"  * Total Queries Tested   : {len(test_queries)}")
        print(f"  * Total Returned Products: {total_returned}")
        print(f"  * Total Relevant Products: {total_relevant}")
        print(f"  * OVERALL RELEVANCE RATE : {overall_rel_pct:.1f}%")
        print("=" * 80)


def test_ai_retrieval_system():
    run_ai_retrieval_tests()


if __name__ == '__main__':
    run_ai_retrieval_tests()
