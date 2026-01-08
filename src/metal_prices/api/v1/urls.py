"""
URL routing for Metal Prices API v1.
"""
from django.urls import path

from .views import FetchMetalPricesView, MetalPriceDetailView, MetalPriceListView

app_name = "metal_prices"

urlpatterns = [
    # GET /api/v1/metal-prices/
    path("metal-prices/", MetalPriceListView.as_view(), name="metal-price-list"),
    # POST /api/v1/metal-prices/fetch/
    path("metal-prices/fetch/", FetchMetalPricesView.as_view(), name="fetch-metal-prices"),
    # GET /api/v1/metal-prices/{symbol}/
    path("metal-prices/<str:symbol>/", MetalPriceDetailView.as_view(), name="metal-price-detail"),
]
