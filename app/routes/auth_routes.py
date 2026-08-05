from flask import Blueprint, render_template

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login Route"""
    return render_template('main/index.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register Route"""
    return render_template('main/index.html')


@auth_bp.route('/logout')
def logout():
    """Logout Route"""
    return render_template('main/index.html')
