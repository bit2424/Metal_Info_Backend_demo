"""
Serializers for Metal Prices API.
"""
from rest_framework import serializers

from metal_prices.models import MetalPrice


class PricePointSerializer(serializers.Serializer):
    """Serializer for price history points."""

    date = serializers.IntegerField(help_text="Unix timestamp in milliseconds")
    priceNormalised = serializers.FloatField(help_text="Normalized price value")
    priceType = serializers.CharField(help_text="Type of price (e.g., spot, future)")


class MetalPriceSerializer(serializers.ModelSerializer):
    """Serializer for MetalPrice model."""

    price_history = serializers.JSONField(read_only=True)
    price_history_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = MetalPrice
        fields = [
            "uuid",
            "symbol",
            "name",
            "price_usd",
            "unit",
            "indicator_one",
            "indicator_two",
            "indicator_three",
            "chart_indicator",
            "last_date",
            "price_history",
            "price_history_count",
            "fetched_at",
            "created_at",
        ]
        read_only_fields = fields


class MetalPriceSummarySerializer(serializers.Serializer):
    """Serializer for fetch response summary."""

    symbol = serializers.CharField()
    chart_indicator = serializers.DecimalField(max_digits=20, decimal_places=10)
    indicator_one = serializers.DecimalField(max_digits=20, decimal_places=10)
    price_history_count = serializers.IntegerField()


class FetchRequestSerializer(serializers.Serializer):
    """Serializer for the fetch endpoint request."""

    metals = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Optional list of metal symbols to fetch"
    )


class FetchResponseSerializer(serializers.Serializer):
    """Serializer for the fetch endpoint response."""

    success = serializers.BooleanField()
    message = serializers.CharField()
    inserted = serializers.IntegerField()
    fetched_at = serializers.DateTimeField()
    prices = MetalPriceSummarySerializer(many=True)


class ErrorResponseSerializer(serializers.Serializer):
    """Serializer for error responses."""

    success = serializers.BooleanField(default=False)
    error = serializers.CharField()
