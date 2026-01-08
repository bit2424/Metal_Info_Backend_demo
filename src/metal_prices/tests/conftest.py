"""
Pytest fixtures for Metal Prices tests.
"""
import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from metal_prices.tests.factories import MetalPriceFactory


@pytest.fixture
def api_client():
    """Provide an API client for testing."""
    return APIClient()


@pytest.fixture
def sample_metal_prices():
    """Create a batch of metal prices with the same fetched_at timestamp."""
    fetched_at = timezone.now()
    return [
        MetalPriceFactory(symbol="Tense", fetched_at=fetched_at),
        MetalPriceFactory(symbol="Troma", fetched_at=fetched_at),
        MetalPriceFactory(symbol="Zorba", fetched_at=fetched_at),
    ]


@pytest.fixture
def mock_api_response():
    """Mock response from external metal prices API."""
    return [
        {
            "material": "Tense",
            "indicatorOne": 0.0234,
            "indicatorTwo": -0.0156,
            "indicatorThree": 0.0089,
            "chartIndicator": 0.0167,
            "lastDate": 1736294400000,
            "prices": [
                {
                    "date": 1735689600000,
                    "priceNormalised": 0.9823,
                    "priceType": "spot"
                },
                {
                    "date": 1735776000000,
                    "priceNormalised": 0.9856,
                    "priceType": "spot"
                }
            ]
        },
        {
            "material": "Troma",
            "indicatorOne": 0.0145,
            "indicatorTwo": -0.0089,
            "indicatorThree": 0.0123,
            "chartIndicator": 0.0098,
            "lastDate": 1736294400000,
            "prices": [
                {
                    "date": 1735689600000,
                    "priceNormalised": 1.0234,
                    "priceType": "spot"
                }
            ]
        }
    ]


@pytest.fixture
def valid_fetch_payload():
    """Valid payload for fetch endpoint."""
    return {
        "metals": ["Tense", "Troma"]
    }
