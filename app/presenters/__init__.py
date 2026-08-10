"""
Presenters Module - Presenter layer in MVP Architecture.
Formats data retrieved from Services/Models into view-ready models for templates.
"""
from app.presenters.product_presenter import ProductPresenter
from app.presenters.ai_presenter import AIPresenter

__all__ = ['ProductPresenter', 'AIPresenter']

