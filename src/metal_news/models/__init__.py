"""
Models for metal_news app.
"""
from .keyword import Keyword, NewsKeyword
from .metal_news import MetalNews

__all__ = ["MetalNews", "Keyword", "NewsKeyword"]
