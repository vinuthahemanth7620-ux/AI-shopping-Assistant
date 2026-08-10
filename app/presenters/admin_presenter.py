import logging
import json
from urllib.parse import urlencode
from app.services.admin_service import AdminService
from app.services.product_service import ProductService
from app.presenters.product_presenter import ProductPresenter

logger = logging.getLogger(__name__)

class AdminPresenter:
    """
    Admin Presenter Layer - Validates input for Admin CRUD operations,
    formats View-Model objects for dashboard, forms, and product catalog tables.
    Follows MVP Architecture.
    """

    @classmethod
    def validate_product_data(cls, form_data):
        """
        Validate product create/update form payload.
        Returns (is_valid, errors_dict, cleaned_data_dict).
        """
        errors = {}
        cleaned = {}

        # 1. Product Name Validation
        name = form_data.get('name', '').strip()
        if not name:
            errors['name'] = 'Product name is required.'
        elif len(name) > 255:
            errors['name'] = 'Product name cannot exceed 255 characters.'
        else:
            cleaned['name'] = name

        # 2. Brand Validation
        brand = form_data.get('brand', '').strip()
        if not brand:
            errors['brand'] = 'Brand name is required.'
        elif len(brand) > 100:
            errors['brand'] = 'Brand cannot exceed 100 characters.'
        else:
            cleaned['brand'] = brand

        # 3. Category Validation
        category_id_str = form_data.get('category_id', '').strip()
        if not category_id_str:
            errors['category_id'] = 'Please select a product category.'
        else:
            try:
                cat_id = int(category_id_str)
                if cat_id <= 0:
                    errors['category_id'] = 'Invalid category selected.'
                else:
                    cleaned['category_id'] = cat_id
            except (ValueError, TypeError):
                errors['category_id'] = 'Invalid category format.'

        # 4. Price Validation
        price_str = form_data.get('price', '').strip()
        if not price_str:
            errors['price'] = 'Price is required.'
        else:
            try:
                price = float(price_str)
                if price < 0:
                    errors['price'] = 'Price cannot be negative.'
                else:
                    cleaned['price'] = price
            except (ValueError, TypeError):
                errors['price'] = 'Price must be a valid number.'

        # 5. Rating Validation
        rating_str = form_data.get('rating', '0.0').strip() or '0.0'
        try:
            rating = float(rating_str)
            if not (0.0 <= rating <= 5.0):
                errors['rating'] = 'Rating must be between 0.0 and 5.0.'
            else:
                cleaned['rating'] = rating
        except (ValueError, TypeError):
            errors['rating'] = 'Rating must be a valid number between 0.0 and 5.0.'

        # 6. Stock Quantity Validation
        stock_str = form_data.get('stock_quantity', '0').strip() or '0'
        try:
            stock = int(stock_str)
            if stock < 0:
                errors['stock_quantity'] = 'Stock quantity cannot be negative.'
            else:
                cleaned['stock_quantity'] = stock
        except (ValueError, TypeError):
            errors['stock_quantity'] = 'Stock quantity must be a valid integer.'

        # 7. Description
        description = form_data.get('description', '').strip()
        cleaned['description'] = description

        # 8. Image URL
        image_url = form_data.get('image_url', '').strip()
        if image_url and not (image_url.startswith('http://') or image_url.startswith('https://') or image_url.startswith('/')):
            image_url = f"/{image_url}"
        cleaned['image_url'] = image_url

        # 9. Availability
        cleaned['is_available'] = form_data.get('is_available', 'true').lower() in ['true', '1', 'on', 'yes']

        # 10. Specifications JSON or Key-Value pairs
        specs_input = form_data.get('specifications', '')
        if isinstance(specs_input, str) and specs_input.strip():
            try:
                specs_dict = json.loads(specs_input)
                cleaned['specifications'] = specs_dict
            except json.JSONDecodeError:
                # Parse key: value per line format
                lines = specs_input.strip().split('\n')
                specs_dict = {}
                for line in lines:
                    if ':' in line:
                        k, v = line.split(':', 1)
                        specs_dict[k.strip()] = v.strip()
                cleaned['specifications'] = specs_dict
        elif isinstance(specs_input, dict):
            cleaned['specifications'] = specs_input
        else:
            cleaned['specifications'] = {}

        # SKU & Slug optional
        cleaned['sku'] = form_data.get('sku', '').strip()
        cleaned['slug'] = form_data.get('slug', '').strip()

        is_valid = len(errors) == 0
        return is_valid, errors, cleaned

    @classmethod
    def prepare_dashboard_view(cls):
        """
        Prepare view-model data object for admin dashboard.
        """
        stats = AdminService.get_dashboard_stats()
        recent_models = AdminService.get_recent_products(limit=6)
        recent_cards = [ProductPresenter.format_product_card(p) for p in recent_models]

        return {
            'stats': stats,
            'recent_products': recent_cards
        }

    @classmethod
    def prepare_products_list_view(cls, query_params):
        """
        Prepare view-model data object for admin products management page.
        """
        q = query_params.get('q', '').strip()
        category_id = query_params.get('category', '').strip()
        stock_status = query_params.get('stock', '').strip()
        page = query_params.get('page', 1, type=int)

        pagination = AdminService.get_admin_filtered_products(
            search_query=q,
            category_id=category_id,
            stock_status=stock_status,
            page=page,
            per_page=10
        )

        categories = ProductService.get_all_categories()
        product_cards = [ProductPresenter.format_product_card(p) for p in pagination.items]

        # URL builder helper for pagination links
        def get_page_url(page_number):
            params = {}
            if q: params['q'] = q
            if category_id: params['category'] = category_id
            if stock_status: params['stock'] = stock_status
            params['page'] = page_number
            return f"/admin/products?{urlencode(params)}"

        category_options = [
            {
                'id': cat.id,
                'name': cat.name,
                'is_selected': str(cat.id) == category_id
            } for cat in categories
        ]

        return {
            'products': product_cards,
            'total_count': pagination.total,
            'page': pagination.page,
            'pages': pagination.pages,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next,
            'prev_num': pagination.prev_num,
            'next_num': pagination.next_num,
            'get_page_url': get_page_url,
            'categories': category_options,
            'query_params': {
                'q': q,
                'category': category_id,
                'stock': stock_status
            }
        }
