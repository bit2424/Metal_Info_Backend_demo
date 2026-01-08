from django.contrib import admin

from .models import MetalPrice


@admin.register(MetalPrice)
class MetalPriceAdmin(admin.ModelAdmin):
    """Admin interface for MetalPrice model."""

    list_display = [
        "symbol",
        "name",
        "price_usd",
        "chart_indicator",
        "fetched_at",
        "created_at",
    ]
    list_filter = ["symbol", "fetched_at", "created_at"]
    search_fields = ["symbol", "name"]
    readonly_fields = ["uuid", "created_at", "updated_at"]
    ordering = ["-fetched_at", "symbol"]

    fieldsets = (
        ("Basic Information", {
            "fields": ("uuid", "symbol", "name", "price_usd", "unit")
        }),
        ("Indicators", {
            "fields": ("indicator_one", "indicator_two", "indicator_three", "chart_indicator")
        }),
        ("Timestamps", {
            "fields": ("last_date", "fetched_at", "created_at", "updated_at")
        }),
        ("Historical Data", {
            "fields": ("price_history",),
            "classes": ("collapse",)
        }),
    )
