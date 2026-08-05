from flask import Blueprint

planner_bp = Blueprint('planner', __name__)


@planner_bp.route('/')
def shopping_planner():
    """Shopping Planner Blueprint Placeholder Route"""
    return "Shopping Planner Module Coming Soon"
