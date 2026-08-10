import re
import json
import logging
from datetime import datetime
from sqlalchemy import or_, func
from app import db
from app.models.product import Product
from app.models.category import Category

logger = logging.getLogger(__name__)

class AdminService:
    """
    Admin Service Layer - Database queries, analytics, and CRUD operations for products.
    Encapsulates all SQLAlchemy ORM operations for Admin Dashboard.
    Follows MVP Architecture.
    """

    @staticmethod
    def get_dashboard_stats():
        """
        Calculate administrative statistics metrics:
        - Total Products
        - Total Categories
        - Products In Stock
        - Products Out of Stock
        - Average Product Rating
        """
        try:
            total_products = Product.query.filter(Product.is_active == True).count()
            total_categories = Category.query.filter(Category.is_active == True).count()
            in_stock = Product.query.filter(Product.is_active == True, Product.stock_quantity > 0, Product.is_available == True).count()
            out_of_stock = Product.query.filter(Product.is_active == True, or_(Product.stock_quantity == 0, Product.is_available == False)).count()
            
            avg_rating_res = db.session.query(func.avg(Product.rating)).filter(Product.is_active == True).scalar()
            avg_rating = round(float(avg_rating_res), 2) if avg_rating_res is not None else 0.0

            return {
                'total_products': total_products,
                'total_categories': total_categories,
                'in_stock': in_stock,
                'out_of_stock': out_of_stock,
                'average_rating': avg_rating
            }
        except Exception as e:
            logger.error(f"Error calculating dashboard stats: {str(e)}")
            return {
                'total_products': 0,
                'total_categories': 0,
                'in_stock': 0,
                'out_of_stock': 0,
                'average_rating': 0.0
            }

    @staticmethod
    def get_recent_products(limit=5):
        """Retrieve most recently added active products."""
        return Product.query.filter(Product.is_active == True).order_by(Product.id.desc()).limit(limit).all()

    @classmethod
    def get_admin_filtered_products(cls, search_query=None, category_id=None, stock_status=None, page=1, per_page=10):
        """
        Query products applying admin filters and pagination.
        """
        query = Product.query.filter(Product.is_active == True)

        # 1. Search Query
        if search_query and search_query.strip():
            term = f"%{search_query.strip()}%"
            query = query.filter(
                or_(
                    Product.name.ilike(term),
                    Product.brand.ilike(term),
                    Product.sku.ilike(term),
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

        # 3. Stock Status Filter
        if stock_status:
            if stock_status == 'in_stock':
                query = query.filter(Product.stock_quantity > 0, Product.is_available == True)
            elif stock_status == 'out_of_stock':
                query = query.filter(or_(Product.stock_quantity == 0, Product.is_available == False))

        # Order by newest
        query = query.order_by(Product.id.desc())

        # Pagination
        try:
            page_num = max(1, int(page))
        except (ValueError, TypeError):
            page_num = 1

        return query.paginate(page=page_num, per_page=per_page, error_out=False)

    @classmethod
    def create_product(cls, data):
        """
        Create a new product in MySQL catalog.
        """
        name = data.get('name', '').strip()
        brand = data.get('brand', '').strip()
        category_id = int(data.get('category_id'))
        price = float(data.get('price', 0))
        rating = float(data.get('rating', 0.0))
        stock_quantity = int(data.get('stock_quantity', 0))
        description = data.get('description', '').strip()
        image_url = data.get('image_url', '').strip() or None
        is_available = bool(data.get('is_available', True))

        # Generate SKU if not specified
        sku = data.get('sku', '').strip()
        if not sku:
            sku = f"PRD{int(datetime.utcnow().timestamp())}"

        # Generate Slug
        slug = data.get('slug', '').strip()
        if not slug:
            slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
            if not slug:
                slug = f"product-{int(datetime.utcnow().timestamp())}"

        # Ensure slug uniqueness
        existing_slug = Product.query.filter_by(slug=slug).first()
        if existing_slug:
            slug = f"{slug}-{int(datetime.utcnow().timestamp())}"

        # Process specifications dictionary/JSON
        specifications = data.get('specifications', {})
        if isinstance(specifications, str):
            try:
                specifications = json.loads(specifications)
            except Exception:
                specifications = {}

        new_product = Product(
            sku=sku,
            slug=slug,
            name=name,
            brand=brand,
            category_id=category_id,
            price=price,
            rating=rating,
            stock_quantity=stock_quantity,
            description=description,
            image_url=image_url,
            is_available=is_available,
            is_active=True,
            specifications=specifications
        )

        db.session.add(new_product)
        db.session.commit()
        return new_product

    @classmethod
    def update_product(cls, product_id, data):
        """
        Update an existing product by ID.
        """
        product = Product.query.filter_by(id=product_id, is_active=True).first()
        if not product:
            return None

        product.name = data.get('name', product.name).strip()
        product.brand = data.get('brand', product.brand).strip()
        
        if 'category_id' in data and data['category_id']:
            product.category_id = int(data['category_id'])

        if 'price' in data:
            product.price = float(data['price'])

        if 'rating' in data:
            product.rating = float(data['rating'])

        if 'stock_quantity' in data:
            product.stock_quantity = int(data['stock_quantity'])

        if 'description' in data:
            product.description = data['description'].strip()

        if 'image_url' in data:
            product.image_url = data['image_url'].strip() or None

        if 'is_available' in data:
            product.is_available = bool(data['is_available'])

        if 'specifications' in data:
            specs = data['specifications']
            if isinstance(specs, str):
                try:
                    specs = json.loads(specs)
                except Exception:
                    specs = product.specifications
            product.specifications = specs

        product.updated_at = datetime.utcnow()
        db.session.commit()
        return product

    @classmethod
    def delete_product(cls, product_id):
        """
        Delete a product by primary key ID.
        """
        product = Product.query.filter_by(id=product_id).first()
        if not product:
            return False

        db.session.delete(product)
        db.session.commit()
        return True
