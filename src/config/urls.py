"""
URL configuration for Metal Info Backend project.
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.admin_view),
    path("api/v1/", include("metal_prices.api.v1.urls")),
]
