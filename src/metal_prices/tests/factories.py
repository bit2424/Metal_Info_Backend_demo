"""
Factory Boy factories for Metal Prices tests.
"""
from decimal import Decimal

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyDecimal, FuzzyText

from metal_prices.models import MetalPrice


class MetalPriceFactory(DjangoModelFactory):
    """Factory for creating MetalPrice instances."""

    class Meta:
        model = MetalPrice

    symbol = FuzzyChoice(
        [
            "Aroma",
            "Berry",
            "Birch",
            "Candy",
            "Cliff",
            "Clove",
            "Elmo",
            "Taldon",
            "Tainttabor",
            "Tense",
            "Troma",
            "Zorba",
        ]
    )
    name = factory.LazyAttribute(lambda obj: obj.symbol)
    price_usd = FuzzyDecimal(low=0.5, high=2.0, precision=10)
    unit = "normalized"
    indicator_one = FuzzyDecimal(low=-0.1, high=0.1, precision=10)
    indicator_two = FuzzyDecimal(low=-0.1, high=0.1, precision=10)
    indicator_three = FuzzyDecimal(low=-0.1, high=0.1, precision=10)
    chart_indicator = FuzzyDecimal(low=-0.05, high=0.05, precision=10)
    last_date = factory.LazyFunction(timezone.now)
    fetched_at = factory.LazyFunction(timezone.now)
    price_history = factory.LazyFunction(
        lambda: [
            {
                "date": 1735689600000,
                "priceNormalised": 0.9823,
                "priceType": "spot"
            },
            {
                "date": 1735776000000,
                "priceNormalised": 0.9856,
                "priceType": "spot"
            },
        ]
    )


class MetalPriceWithSameFetchTimeFactory(DjangoModelFactory):
    """Factory for creating MetalPrice instances with the same fetch time."""

    class Meta:
        model = MetalPrice

    symbol = FuzzyChoice(
        [
            "Aroma",
            "Berry",
            "Birch",
            "Candy",
            "Cliff",
            "Clove",
            "Elmo",
            "Taldon",
            "Tainttabor",
            "Tense",
            "Troma",
            "Zorba",
        ]
    )
    name = factory.LazyAttribute(lambda obj: obj.symbol)
    price_usd = FuzzyDecimal(low=0.5, high=2.0, precision=10)
    unit = "normalized"
    indicator_one = FuzzyDecimal(low=-0.1, high=0.1, precision=10)
    indicator_two = FuzzyDecimal(low=-0.1, high=0.1, precision=10)
    indicator_three = FuzzyDecimal(low=-0.1, high=0.1, precision=10)
    chart_indicator = FuzzyDecimal(low=-0.05, high=0.05, precision=10)
    last_date = factory.LazyFunction(timezone.now)
    # Use a fixed fetched_at for batch operations
    fetched_at = factory.LazyFunction(lambda: timezone.now())
    price_history = factory.LazyFunction(
        lambda: [
            {
                "date": 1735689600000,
                "priceNormalised": 0.9823,
                "priceType": "spot"
            },
        ]
    )
