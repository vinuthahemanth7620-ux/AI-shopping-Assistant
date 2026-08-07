from flask import Blueprint, render_template
from flask_login import login_required, current_user

planner_bp = Blueprint('planner', __name__)


@planner_bp.route('/')
@login_required
def shopping_planner():
    """Protected Shopping Planner Route"""
    return render_template('main/index.html')
