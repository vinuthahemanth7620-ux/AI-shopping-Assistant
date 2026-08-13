from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.shopping_planner import ShoppingPlanner
from app.models.product import Product
from app.presenters.product_presenter import ProductPresenter

planner_bp = Blueprint('planner', __name__)


@planner_bp.route('/', methods=['GET', 'POST'])
@login_required
def shopping_planner():
    """
    Protected Shopping Planner Route.
    Allows users to set target shopping budgets, organize bucket lists, and calculate budget allocation.
    """
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            title = request.form.get('title', '').strip()
            target_budget = request.form.get('target_budget', type=float) or 0.0

            if title:
                plan_item = ShoppingPlanner(
                    user_id=current_user.id,
                    plan_name=title,
                    budget=target_budget
                )
                db.session.add(plan_item)
                db.session.commit()
                flash(f'Added "{title}" to your Shopping Planner!', 'success')
            return redirect(url_for('planner.shopping_planner'))

        elif action == 'delete':
            item_id = request.form.get('item_id', type=int)
            plan_item = ShoppingPlanner.query.filter_by(id=item_id, user_id=current_user.id).first()
            if plan_item:
                db.session.delete(plan_item)
                db.session.commit()
                flash('Item removed from Shopping Planner.', 'info')
            return redirect(url_for('planner.shopping_planner'))

    # Load logged-in user's planner items
    planner_items = ShoppingPlanner.query.filter_by(user_id=current_user.id).order_by(ShoppingPlanner.created_at.desc()).all()
    
    total_budget = sum(float(item.budget or 0.0) for item in planner_items)
    
    # Load top recommended budget options
    recommended_gadgets = Product.query.filter_by(is_active=True).order_by(Product.rating.desc()).limit(6).all()
    formatted_gadgets = [ProductPresenter.format_product_card(p) for p in recommended_gadgets]

    return render_template(
        'planner.html',
        planner_items=planner_items,
        total_budget=total_budget,
        total_budget_formatted=f"₹{total_budget:,.2f}",
        recommended_gadgets=formatted_gadgets
    )
