"""
URL configuration for Metal News API v1.
"""
from django.urls import path

from .views import (
    FetchMetalNewsView,
    KeywordListView,
    MetalNewsDetailView,
    MetalNewsListView,
    MetalNewsSearchView,
)

app_name = "metal_news"

urlpatterns = [
    path("metal-news/", MetalNewsListView.as_view(), name="metal-news-list"),
    path("metal-news/search/", MetalNewsSearchView.as_view(), name="metal-news-search"),
    path("metal-news/fetch/", FetchMetalNewsView.as_view(), name="metal-news-fetch"),
    path("metal-news/<uuid:uuid>/", MetalNewsDetailView.as_view(), name="metal-news-detail"),
    path("keywords/", KeywordListView.as_view(), name="keywords-list"),
]
