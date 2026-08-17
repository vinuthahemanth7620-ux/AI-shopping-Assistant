from sqlalchemy import or_, and_, func, case
from sqlalchemy.orm import joinedload
from app import db
from app.models.product import Product
from app.models.category import Category

USD_TO_INR = 83.0


class ProductService:
    """
    Product Service Layer - Database queries, search, filter, sort, and pagination.
    Encapsulates all SQLAlchemy ORM operations for products and categories.
    """
    _BRANDS_CACHE = None
    _PRICE_BOUNDS_CACHE = None

    @classmethod
    def invalidate_caches(cls):
        """Invalidate in-memory caches when products are created, updated, or deleted."""
        cls._BRANDS_CACHE = None
        cls._PRICE_BOUNDS_CACHE = None

    @classmethod
    def get_all_categories(cls):
        """Retrieve all active categories ordered by name."""
        return Category.query.filter_by(is_active=True).order_by(Category.name.asc()).all()

    @classmethod
    def get_all_brands(cls):
        """Retrieve all distinct brands from active products (cached)."""
        if cls._BRANDS_CACHE is not None:
            return cls._BRANDS_CACHE
        results = db.session.query(Product.brand)\
            .filter(Product.is_active == True)\
            .distinct()\
            .order_by(Product.brand.asc())\
            .all()
        cls._BRANDS_CACHE = [r[0] for r in results if r[0]]
        return cls._BRANDS_CACHE

    @classmethod
    def get_price_bounds(cls):
        """Get the minimum and maximum normalized price (INR) across active products for filter inputs (cached)."""
        if cls._PRICE_BOUNDS_CACHE is not None:
            return cls._PRICE_BOUNDS_CACHE
        norm_expr = case((and_(Product.category_id > 4, Product.price < 3000.0), Product.price * USD_TO_INR), else_=Product.price)
        min_p = db.session.query(func.min(norm_expr)).filter(Product.is_active == True).scalar()
        max_p = db.session.query(func.max(norm_expr)).filter(Product.is_active == True).scalar()
        
        cls._PRICE_BOUNDS_CACHE = {
            'min_price': float(min_p) if min_p is not None else 0.0,
            'max_price': float(max_p) if max_p is not None else 1000000.0
        }
        return cls._PRICE_BOUNDS_CACHE

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
        """
        query = Product.query.options(joinedload(Product.category)).filter(Product.is_active == True)

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

        # 4. Dual-Currency Price Range Filter
        if min_price is not None:
            try:
                min_p_val = float(min_price)
                usd_min = min_p_val / USD_TO_INR
                query = query.filter(
                    or_(
                        and_(or_(Product.category_id <= 4, Product.price >= 3000.0), Product.price >= min_p_val),
                        and_(Product.category_id > 4, Product.price < 3000.0, Product.price >= usd_min)
                    )
                )
            except (ValueError, TypeError):
                pass

        if max_price is not None:
            try:
                max_p_val = float(max_price)
                usd_max = max_p_val / USD_TO_INR
                query = query.filter(
                    or_(
                        and_(or_(Product.category_id <= 4, Product.price >= 3000.0), Product.price <= max_p_val),
                        and_(Product.category_id > 4, Product.price < 3000.0, Product.price <= usd_max)
                    )
                )
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

        # 6. Sorting with Normalized INR Expression
        norm_price_expr = case((and_(Product.category_id > 4, Product.price < 3000.0), Product.price * USD_TO_INR), else_=Product.price)

        if sort_by == 'price_asc':
            query = query.order_by(norm_price_expr.asc(), Product.id.desc())
        elif sort_by == 'price_desc':
            query = query.order_by(norm_price_expr.desc(), Product.id.desc())
        elif sort_by == 'rating_desc':
            query = query.order_by(Product.rating.desc(), Product.id.desc())
        elif sort_by == 'name_asc':
            query = query.order_by(Product.name.asc(), Product.id.desc())
        else:
            query = query.order_by(Product.id.desc())

        # 7. Pagination
        try:
            page_num = max(1, int(page))
        except (ValueError, TypeError):
            page_num = 1

        pagination = query.paginate(page=page_num, per_page=per_page, error_out=False)
        return pagination
