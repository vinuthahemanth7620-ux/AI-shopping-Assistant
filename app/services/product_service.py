from sqlalchemy import or_, func
from app import db
from app.models.product import Product
from app.models.category import Category


class ProductService:
    """
    Product Service Layer - Database queries, search, filter, sort, and pagination.
    Encapsulates all SQLAlchemy ORM operations for products and categories.
    """

    @staticmethod
    def get_all_categories():
        """Retrieve all active categories ordered by name."""
        return Category.query.filter_by(is_active=True).order_by(Category.name.asc()).all()

    @staticmethod
    def get_all_brands():
        """Retrieve all distinct brands from active products."""
        results = db.session.query(Product.brand)\
            .filter(Product.is_active == True)\
            .distinct()\
            .order_by(Product.brand.asc())\
            .all()
        return [r[0] for r in results if r[0]]

    @staticmethod
    def get_price_bounds():
        """Get the minimum and maximum price across active products for filter inputs."""
        min_p, max_p = db.session.query(
            func.min(Product.price),
            func.max(Product.price)
        ).filter(Product.is_active == True).first()
        
        return {
            'min_price': float(min_p) if min_p is not None else 0.0,
            'max_price': float(max_p) if max_p is not None else 1000000.0
        }

    @staticmethod
    def get_product_by_id(product_id):
        """
        Retrieve a single product by its primary key ID.
        Returns Product instance or None if not found or inactive.
        """
        if not isinstance(product_id, int) or product_id <= 0:
            return None
        return Product.query.filter_by(id=product_id, is_active=True).first()

    @classmethod
    def get_filtered_products(cls, search_query=None, category_id=None, brand=None,
                              min_price=None, max_price=None, min_rating=None,
                              sort_by='newest', page=1, per_page=12):
        """
        Query products applying search, category, brand, price range, rating filters, and sorting.
        
        :param search_query: Text to search in name, brand, and description
        :param category_id: Category ID filter
        :param brand: Brand name filter
        :param min_price: Minimum price filter
        :param max_price: Maximum price filter
        :param min_rating: Minimum rating filter (e.g. 4.0)
        :param sort_by: Sorting field identifier ('price_asc', 'price_desc', 'rating_desc', 'name_asc', 'newest')
        :param page: Current page number
        :param per_page: Items per page (default: 12)
        :return: Pagination object containing items, total, pages, current page, etc.
        """
        # Base query for active products
        query = Product.query.filter(Product.is_active == True)

        # 1. Search Query (Name, Brand, Description)
        if search_query:
            term = f"%{search_query.strip()}%"
            query = query.filter(
                or_(
                    Product.name.ilike(term),
                    Product.brand.ilike(term),
                    Product.description.ilike(term)
                )
            )

        # 2. Category Filter
        if category_id:
            try:
                cat_id_int = int(category_id)
                if cat_id_int > 0:
                    query = query.filter(Product.category_id == cat_id_int)
            except (ValueError, TypeError):
                pass

        # 3. Brand Filter
        if brand and str(brand).strip():
            query = query.filter(Product.brand == str(brand).strip())

        # 4. Price Range Filter
        if min_price is not None:
            try:
                min_p_val = float(min_price)
                query = query.filter(Product.price >= min_p_val)
            except (ValueError, TypeError):
                pass

        if max_price is not None:
            try:
                max_p_val = float(max_price)
                query = query.filter(Product.price <= max_p_val)
            except (ValueError, TypeError):
                pass

        # 5. Rating Filter
        if min_rating is not None:
            try:
                min_r_val = float(min_rating)
                if 0.0 <= min_r_val <= 5.0:
                    query = query.filter(Product.rating >= min_r_val)
            except (ValueError, TypeError):
                pass

        # 6. Sorting (With Product.id.desc() secondary tie-breaker for deterministic pagination)
        if sort_by == 'price_asc':
            query = query.order_by(Product.price.asc(), Product.id.desc())
        elif sort_by == 'price_desc':
            query = query.order_by(Product.price.desc(), Product.id.desc())
        elif sort_by == 'rating_desc':
            query = query.order_by(Product.rating.desc(), Product.id.desc())
        elif sort_by == 'name_asc':
            query = query.order_by(Product.name.asc(), Product.id.desc())
        else:  # Default: newest / id desc
            query = query.order_by(Product.id.desc())

        # 7. Pagination
        try:
            page_num = max(1, int(page))
        except (ValueError, TypeError):
            page_num = 1

        pagination = query.paginate(page=page_num, per_page=per_page, error_out=False)
        return pagination
