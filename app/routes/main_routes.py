from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app import db
from app.utils.decorators import admin_required
from app.models.category import Category
from app.models.product import Product
from app.models.contact_message import ContactMessage
from app.presenters.product_presenter import ProductPresenter

main_bp = Blueprint('main', __name__)



@main_bp.route('/')
def index():
    """Public Landing Page Route with Real E-Commerce Catalog Data"""
    # 1. Fetch Active Categories
    db_categories = Category.query.filter_by(is_active=True).order_by(Category.name.asc()).all()
    
    category_icon_map = {
        'laptops': 'fa-laptop',
        'mobiles': 'fa-mobile-screen-button',
        'headphones': 'fa-headphones',
        'smart-watches': 'fa-stopwatch',
        'camera-and-photo': 'fa-camera',
        'amazon-home': 'fa-house-laptop',
        'all-beauty': 'fa-wand-magic',
        'amazon-fashion': 'fa-shirt',
        'sports-and-outdoors': 'fa-basketball',
        'automotive': 'fa-car',
        'tools-and-home-improvement': 'fa-screwdriver-wrench',
        'toys-and-games': 'fa-gamepad',
        'computers': 'fa-desktop',
        'appliances': 'fa-blender'
    }

    formatted_categories = []
    for cat in db_categories:
        icon_cls = category_icon_map.get(cat.slug, 'fa-boxes-stacked')
        prod_count = Product.query.filter_by(category_id=cat.id, is_active=True).count()
        formatted_categories.append({
            'id': cat.id,
            'name': cat.name,
            'slug': cat.slug,
            'icon': icon_cls,
            'product_count': prod_count
        })

    # Limit categories for homepage grid (top 12 categories with active products)
    formatted_categories = [c for c in formatted_categories if c['product_count'] > 0][:12]

    # 2. Fetch Featured Products (Top Rated)
    featured_raw = Product.query.filter_by(is_active=True)\
        .order_by(Product.rating.desc(), Product.id.asc()).limit(8).all()
    featured_products = [ProductPresenter.format_product_card(p) for p in featured_raw]

    # 3. Fetch Today's Best Deals (High Ratings / High Stock)
    deals_raw = Product.query.filter(Product.is_active == True, Product.rating >= 4.0)\
        .order_by(Product.rating.desc(), Product.stock_quantity.desc()).limit(4).all()
    deals_products = [ProductPresenter.format_product_card(p) for p in deals_raw]

    # 4. Fetch New Arrivals (Recently Added)
    arrivals_raw = Product.query.filter_by(is_active=True)\
        .order_by(Product.created_at.desc()).limit(4).all()
    new_arrivals = [ProductPresenter.format_product_card(p) for p in arrivals_raw]

    return render_template(
        'main/index.html',
        categories=formatted_categories,
        featured_products=featured_products,
        deals_products=deals_products,
        new_arrivals=new_arrivals
    )


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Protected User Dashboard Route"""
    return render_template('main/dashboard.html')


@main_bp.route('/admin')
@admin_required
def admin_dashboard():
    """Redirect legacy /admin route to admin.dashboard"""
    return redirect(url_for('admin.dashboard'))


@main_bp.route('/about')
def about():
    """Public About Us Information Page Route"""
    return render_template('about.html')


@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Public Contact Us Page Route & Form Handler"""
    from app.models.team_member import TeamMember
    official_members = TeamMember.query.filter_by(is_official=True).all()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        # Validation
        if not name:
            flash('Please enter your full name.', 'danger')
            return render_template('contact.html', official_members=official_members, name=name, email=email, subject=subject, message=message)

        if not email or '@' not in email or '.' not in email:
            flash('Please enter a valid email address.', 'danger')
            return render_template('contact.html', official_members=official_members, name=name, email=email, subject=subject, message=message)

        if not subject:
            flash('Please enter a subject for your message.', 'danger')
            return render_template('contact.html', official_members=official_members, name=name, email=email, subject=subject, message=message)

        if not message:
            flash('Please enter your message text.', 'danger')
            return render_template('contact.html', official_members=official_members, name=name, email=email, subject=subject, message=message)

        try:
            msg_record = ContactMessage(
                name=name,
                email=email,
                subject=subject,
                message=message,
                status='unread'
            )
            db.session.add(msg_record)
            db.session.commit()
            flash('Thank you for contacting us! Your message has been sent successfully.', 'success')
            return redirect(url_for('main.contact'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while saving your message. Please try again later.', 'danger')
            return render_template('contact.html', official_members=official_members, name=name, email=email, subject=subject, message=message)

    return render_template('contact.html', official_members=official_members)





