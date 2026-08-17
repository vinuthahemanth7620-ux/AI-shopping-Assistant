import re
from urllib.parse import urlencode


class ProductPresenter:
    """
    Product Presenter Layer - Converts SQLAlchemy Product models & query parameters 
    into clean, view-ready dictionaries for Jinja2 Bootstrap templates.
    Follows MVP Architecture.
    """

    DEFAULT_IMAGE = "/static/images/placeholder_product.svg"

    @classmethod
    def clean_image_url(cls, raw_url):
        """
        Centralized, reusable image URL normalizer.
        Handles:
        - Direct HTTP/HTTPS URLs
        - Relative static paths (/static/...)
        - Markdown image links ![alt](url) or [text](url)
        - JSON/Python lists of URLs ["url1", "url2"]
        - Null, None, NaN, empty strings, invalid strings
        - Unsafe script schemes (javascript:, vbscript:, data:text/html)
        """
        if raw_url is None:
            return cls.DEFAULT_IMAGE

        if isinstance(raw_url, (list, tuple)):
            for item in raw_url:
                cleaned = cls.clean_image_url(item)
                if cleaned != cls.DEFAULT_IMAGE:
                    return cleaned
            return cls.DEFAULT_IMAGE

        url_str = str(raw_url).strip()
        if not url_str or url_str.lower() in ['none', 'nan', 'null', '[]', '{}', 'undefined']:
            return cls.DEFAULT_IMAGE

        # Prevent unsafe URI schemes
        if url_str.lower().startswith(('javascript:', 'vbscript:', 'data:text/html')):
            return cls.DEFAULT_IMAGE

        # 1. Parse JSON list string if formatted like ["url1", "url2"]
        if url_str.startswith('[') and url_str.endswith(']'):
            try:
                import json
                parsed = json.loads(url_str)
                if isinstance(parsed, list):
                    for item in parsed:
                        cleaned = cls.clean_image_url(item)
                        if cleaned != cls.DEFAULT_IMAGE:
                            return cleaned
            except Exception:
                pass

        # 2. Extract URL from Markdown link/image format ![alt](url) or [text](url)
        md_match = re.search(r'\((https?://[^\)]+)\)', url_str)
        if md_match:
            return md_match.group(1).strip()

        # 3. Extract HTTP/HTTPS URL from any surrounding text or brackets
        http_match = re.search(r'https?://[^\s\]\)\"\']+', url_str)
        if http_match:
            extracted = http_match.group(0).strip()
            extracted = re.sub(r'[\,\"\']+$', '', extracted)
            return extracted

        # 4. Handle relative local static paths
        if url_str.startswith('static/') or url_str.startswith('/static/'):
            if not url_str.startswith('/'):
                return f"/{url_str}"
            return url_str

        # 5. Relative paths starting with /
        if url_str.startswith('/') and len(url_str) > 1 and not url_str.startswith('//'):
            return url_str

        # 6. Fallback if not a valid URL or path
        return cls.DEFAULT_IMAGE

    @classmethod
    def get_normalized_price_inr(cls, product_or_price, category_id=None):
        """Single central source of truth for normalized INR price calculation."""
        if product_or_price is None:
            return 0.0
        if hasattr(product_or_price, 'normalized_price_inr'):
            return float(product_or_price.normalized_price_inr)
        if hasattr(product_or_price, 'price'):
            raw_p = float(getattr(product_or_price, 'price', 0.0) or 0.0)
            cat_id = getattr(product_or_price, 'category_id', 0) or 0
            if cat_id <= 4 or raw_p >= 3000.0:
                return raw_p
            return raw_p * 83.0
        try:
            val = float(product_or_price)
            if category_id and int(category_id) > 4 and val < 3000.0:
                return val * 83.0
            return val
        except (ValueError, TypeError):
            return 0.0

    @classmethod
    def format_price(cls, product_or_price, category_id=None):
        """Format price float/numeric into Indian Rupee standard format (e.g., ₹59,178.17)."""
        norm_p = cls.get_normalized_price_inr(product_or_price, category_id=category_id)
        return f"₹{norm_p:,.2f}"

    @staticmethod
    def format_rating(rating_val):
        """
        Calculate full, half, and empty stars for Bootstrap/FontAwesome star rendering.
        """
        try:
            val = float(rating_val) if rating_val is not None else 0.0
        except (ValueError, TypeError):
            val = 0.0

        val = max(0.0, min(5.0, val))
        full_stars = int(val)
        remainder = val - full_stars
        has_half = remainder >= 0.3 and remainder <= 0.7
        if remainder > 0.7:
            full_stars += 1
            has_half = False
        
        empty_stars = 5 - full_stars - (1 if has_half else 0)

        return {
            'value': f"{val:.1f}",
            'full_stars': full_stars,
            'has_half_star': has_half,
            'empty_stars': max(0, empty_stars)
        }

    @classmethod
    def format_product_card(cls, product):
        """
        Format a single Product model instance for display in product list cards.
        """
        if not product:
            return None

        image_url = cls.clean_image_url(product.image_url)

        from app.services.product_processor import ProductInformationProcessor

        summary = product.display_short_summary if hasattr(product, 'display_short_summary') else ProductInformationProcessor.generate_short_summary(product)
        features = product.display_key_features if hasattr(product, 'display_key_features') else ProductInformationProcessor.extract_important_features(product, limit=3)

        in_stock = product.is_available and product.is_active and (product.stock_quantity > 0)
        norm_p = cls.get_normalized_price_inr(product)

        rec_score = getattr(product, 'recommendation_score', None)
        rec_reason = getattr(product, 'recommendation_reason', None)

        return {
            'id': product.id,
            'sku': product.sku,
            'slug': product.slug,
            'name': product.name,
            'brand': product.brand,
            'category_name': product.category.name if product.category else 'General',
            'category_id': product.category_id,
            'price_formatted': cls.format_price(norm_p),
            'price_raw': norm_p,
            'price_raw_db': float(product.price) if product.price is not None else 0.0,
            'rating': cls.format_rating(product.rating),
            'short_description': summary,
            'important_features': features[:3],
            'image_url': image_url or cls.DEFAULT_IMAGE,
            'stock_quantity': product.stock_quantity,
            'is_available': in_stock,
            'is_active': product.is_active,
            'stock_badge_class': 'bg-success' if in_stock else 'bg-danger',
            'stock_badge_text': 'In Stock' if in_stock else 'Out of Stock',
            'recommendation_score': round(float(rec_score), 1) if rec_score is not None else None,
            'recommendation_reason': rec_reason
        }

    @classmethod
    def format_product_detail(cls, product):
        """
        Format a single Product model instance for the product detail view.
        Separates clean summary/features from complete collapsible specifications.
        """
        card_data = cls.format_product_card(product)
        if not card_data:
            return None

        from app.services.product_processor import ProductInformationProcessor

        # Extract raw specifications
        raw_specs = product.specifications if isinstance(product.specifications, dict) else {}
        
        # Filter high-value specifications (exclude ASIN, package dimensions, internal metadata)
        clean_specs = product.display_important_specifications if hasattr(product, 'display_important_specifications') else ProductInformationProcessor.extract_important_specifications(product)

        # Build Breadcrumbs
        breadcrumbs = [
            {'title': 'Home', 'url': '/'},
            {'title': 'Products', 'url': '/products'},
            {'title': card_data['category_name'], 'url': f"/products?category={product.category_id}"},
            {'title': product.name, 'url': None}
        ]

        card_data.update({
            'full_description': product.description or "No detailed description available.",
            'short_description': product.display_short_summary,
            'important_features': product.display_key_features[:4],
            'clean_specifications': clean_specs,
            'raw_specifications': raw_specs,
            'specifications': clean_specs if clean_specs else raw_specs,
            'created_at_formatted': product.created_at.strftime('%B %d, %Y') if product.created_at else None,
            'breadcrumbs': breadcrumbs
        })

        return card_data

    @classmethod
    def prepare_catalog_view(cls, pagination, categories, brands, query_params, price_bounds):
        """
        Prepare comprehensive View-Model object for products.html catalog template.
        """
        # Format products
        product_cards = [cls.format_product_card(p) for p in pagination.items]

        # Extract current active filter inputs
        q = query_params.get('q', '').strip()
        category_id = query_params.get('category', '').strip()
        brand = query_params.get('brand', '').strip()
        min_price = query_params.get('min_price', '').strip()
        max_price = query_params.get('max_price', '').strip()
        min_rating = query_params.get('min_rating', '').strip()
        sort_by = query_params.get('sort', 'newest').strip()
        page = pagination.page

        # Calculate active filters count
        active_filters_count = 0
        if q: active_filters_count += 1
        if category_id: active_filters_count += 1
        if brand: active_filters_count += 1
        if min_price: active_filters_count += 1
        if max_price: active_filters_count += 1
        if min_rating: active_filters_count += 1

        # Query parameter builder function for pagination links
        def get_page_url(page_number):
            params = {}
            if q: params['q'] = q
            if category_id: params['category'] = category_id
            if brand: params['brand'] = brand
            if min_price: params['min_price'] = min_price
            if max_price: params['max_price'] = max_price
            if min_rating: params['min_rating'] = min_rating
            if sort_by and sort_by != 'newest': params['sort'] = sort_by
            params['page'] = page_number
            return f"/products?{urlencode(params)}"

        # Query parameter builder for removing specific filters
        def get_remove_filter_url(filter_key):
            params = {}
            if q and filter_key != 'q': params['q'] = q
            if category_id and filter_key != 'category': params['category'] = category_id
            if brand and filter_key != 'brand': params['brand'] = brand
            if min_price and filter_key != 'price': params['min_price'] = min_price
            if max_price and filter_key != 'price': params['max_price'] = max_price
            if min_rating and filter_key != 'rating': params['min_rating'] = min_rating
            if sort_by and sort_by != 'newest': params['sort'] = sort_by
            params['page'] = 1
            return f"/products?{urlencode(params)}" if params else "/products"

        # Category list formatted
        category_options = [
            {
                'id': cat.id,
                'name': cat.name,
                'is_selected': str(cat.id) == category_id
            } for cat in categories
        ]

        # Brand list formatted
        brand_options = [
            {
                'name': b,
                'is_selected': b == brand
            } for b in brands
        ]

        # Sort options list
        sort_options = [
            {'value': 'newest', 'label': 'Newest Arrivals', 'is_selected': sort_by == 'newest'},
            {'value': 'price_asc', 'label': 'Price: Low to High', 'is_selected': sort_by == 'price_asc'},
            {'value': 'price_desc', 'label': 'Price: High to Low', 'is_selected': sort_by == 'price_desc'},
            {'value': 'rating_desc', 'label': 'Highest Rating', 'is_selected': sort_by == 'rating_desc'},
            {'value': 'name_asc', 'label': 'Product Name: A to Z', 'is_selected': sort_by == 'name_asc'}
        ]

        # Selected Category Name helper
        selected_category_name = None
        if category_id:
            for cat in categories:
                if str(cat.id) == category_id:
                    selected_category_name = cat.name
                    break

        return {
            'products': product_cards,
            'total_count': pagination.total,
            'page': page,
            'pages': pagination.pages,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next,
            'prev_num': pagination.prev_num,
            'next_num': pagination.next_num,
            'get_page_url': get_page_url,
            'get_remove_filter_url': get_remove_filter_url,
            'active_filters_count': active_filters_count,
            'query_params': {
                'q': q,
                'category': category_id,
                'brand': brand,
                'min_price': min_price,
                'max_price': max_price,
                'min_rating': min_rating,
                'sort': sort_by
            },
            'categories': category_options,
            'brands': brand_options,
            'sort_options': sort_options,
            'selected_category_name': selected_category_name,
            'price_bounds': price_bounds
        }
