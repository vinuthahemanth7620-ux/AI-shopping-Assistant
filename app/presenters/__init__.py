"""
Presenters Module - Presenter layer in MVP Architecture.
Formats data retrieved from Services/Models into view-ready models for templates.
"""
from app.presenters.product_presenter import ProductPresenter
from app.presenters.ai_presenter import AIPresenter
from app.presenters.admin_presenter import AdminPresenter

__all__ = ['ProductPresenter', 'AIPresenter', 'AdminPresenter']


