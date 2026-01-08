"""
Tests for Metal Prices models.
"""
import pytest
from django.utils import timezone

from metal_prices.models import MetalPrice
from metal_prices.tests.factories import MetalPriceFactory


@pytest.mark.django_db
class TestMetalPriceModel:
    """Tests for the MetalPrice model."""

    def test_create_metal_price(self):
        """Test creating a metal price instance."""
        metal_price = MetalPriceFactory(symbol="Tense")

        assert metal_price.uuid is not None
        assert metal_price.symbol == "Tense"
        assert metal_price.name == "Tense"
        assert metal_price.created_at is not None

    def test_metal_price_str_representation(self):
        """Test string representation of metal price."""
        metal_price = MetalPriceFactory(
            symbol="Tense",
            price_usd="0.9856"
        )

        str_repr = str(metal_price)
        assert "Tense" in str_repr
        assert "0.9856" in str_repr

    def test_price_history_count_property(self):
        """Test price_history_count property."""
        metal_price = MetalPriceFactory(
            price_history=[
                {"date": 1735689600000, "priceNormalised": 0.98, "priceType": "spot"},
                {"date": 1735776000000, "priceNormalised": 0.99, "priceType": "spot"},
            ]
        )

        assert metal_price.price_history_count == 2

    def test_price_history_count_empty(self):
        """Test price_history_count when no history."""
        metal_price = MetalPriceFactory(price_history=None)
        assert metal_price.price_history_count == 0

    def test_soft_delete(self):
        """Test that metal prices are soft deleted."""
        metal_price = MetalPriceFactory()
        uuid = metal_price.uuid

        # Delete the object
        metal_price.delete()

        # Should not be in default queryset
        assert not MetalPrice.objects.filter(uuid=uuid).exists()

        # Should be in all_objects queryset
        assert MetalPrice.all_objects.filter(uuid=uuid).exists()

    def test_ordering(self):
        """Test that metal prices are ordered by fetched_at desc, then symbol."""
        now = timezone.now()
        older = now - timezone.timedelta(hours=1)

        metal1 = MetalPriceFactory(symbol="Zorba", fetched_at=now)
        metal2 = MetalPriceFactory(symbol="Tense", fetched_at=now)
        metal3 = MetalPriceFactory(symbol="Aroma", fetched_at=older)

        prices = list(MetalPrice.objects.all())

        # Should be ordered by fetched_at (desc), then symbol (asc)
        assert prices[0] in [metal1, metal2]  # Both have same fetched_at
        assert prices[-1] == metal3  # Oldest
