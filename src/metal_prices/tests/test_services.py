"""
Tests for Metal Prices services.
"""
from unittest import mock

import pytest
import requests

from metal_prices.api.v1.services import ExternalAPIError, MetalPriceService
from metal_prices.models import MetalPrice
from metal_prices.tests.factories import MetalPriceFactory


@pytest.mark.django_db
class TestMetalPriceService:
    """Tests for the MetalPriceService."""

    def setup_method(self):
        """Setup method for each test."""
        self.service = MetalPriceService()

    @mock.patch("requests.get")
    def test_fetch_and_store_prices_success(self, mock_get, mock_api_response):
        """Test successfully fetching and storing metal prices."""
        mock_get.return_value = mock.Mock(
            status_code=200,
            json=lambda: mock_api_response
        )

        result = self.service.fetch_and_store_prices()

        assert result["success"] is True
        assert result["inserted"] == 2
        assert MetalPrice.objects.count() == 2

        # Verify the data was stored correctly
        tense_price = MetalPrice.objects.get(symbol="Tense")
        assert tense_price.name == "Tense"
        assert float(tense_price.indicator_one) == 0.0234

    @mock.patch("requests.get")
    def test_fetch_and_store_prices_with_specific_metals(self, mock_get, mock_api_response):
        """Test fetching specific metals only."""
        mock_get.return_value = mock.Mock(
            status_code=200,
            json=lambda: mock_api_response
        )

        result = self.service.fetch_and_store_prices(metals=["Tense"])

        assert result["success"] is True
        # Should still process both items from mock response
        assert result["inserted"] == 2

    @mock.patch("requests.get")
    def test_fetch_prices_api_connection_error(self, mock_get):
        """Test handling of API connection errors."""
        mock_get.side_effect = requests.ConnectionError("Connection failed")

        with pytest.raises(ExternalAPIError) as exc_info:
            self.service.fetch_and_store_prices()

        assert "Connection failed" in str(exc_info.value)

    @mock.patch("requests.get")
    def test_fetch_prices_api_timeout(self, mock_get):
        """Test handling of API timeout errors."""
        mock_get.side_effect = requests.Timeout("Request timed out")

        with pytest.raises(ExternalAPIError) as exc_info:
            self.service.fetch_and_store_prices()

        assert "timed out" in str(exc_info.value)

    @mock.patch("requests.get")
    def test_fetch_prices_invalid_response_format(self, mock_get):
        """Test handling of invalid API response format."""
        mock_get.return_value = mock.Mock(
            status_code=200,
            json=lambda: {"error": "Invalid format"}  # Dict instead of list
        )

        with pytest.raises(ExternalAPIError) as exc_info:
            self.service.fetch_and_store_prices()

        assert "Invalid API response format" in str(exc_info.value)

    def test_get_latest_prices(self, sample_metal_prices):
        """Test retrieving the latest metal prices."""
        prices = self.service.get_latest_prices()

        assert len(prices) == 3
        assert all(isinstance(p, MetalPrice) for p in prices)

    def test_get_latest_prices_with_symbols_filter(self, sample_metal_prices):
        """Test retrieving latest prices filtered by symbols."""
        prices = self.service.get_latest_prices(symbols=["Tense", "Troma"])

        assert len(prices) == 2
        symbols = [p.symbol for p in prices]
        assert "Tense" in symbols
        assert "Troma" in symbols
        assert "Zorba" not in symbols

    def test_get_latest_prices_empty_db(self):
        """Test retrieving prices when database is empty."""
        prices = self.service.get_latest_prices()
        assert prices == []

    def test_get_price_by_symbol(self, sample_metal_prices):
        """Test retrieving a specific metal price by symbol."""
        price = self.service.get_price_by_symbol("Tense")

        assert price is not None
        assert price.symbol == "Tense"

    def test_get_price_by_symbol_not_found(self):
        """Test retrieving a non-existent metal price."""
        price = self.service.get_price_by_symbol("InvalidMetal")
        assert price is None

    @mock.patch("requests.get")
    def test_process_and_store_skips_invalid_data(self, mock_get):
        """Test that invalid metal data is skipped during processing."""
        invalid_response = [
            {
                # Missing 'material' field
                "indicatorOne": 0.0234,
                "prices": []
            },
            {
                "material": "Tense",
                "indicatorOne": 0.0234,
                "indicatorTwo": -0.0156,
                "indicatorThree": 0.0089,
                "chartIndicator": 0.0167,
                "lastDate": 1736294400000,
                "prices": [
                    {"date": 1735689600000, "priceNormalised": 0.98, "priceType": "spot"}
                ]
            }
        ]

        mock_get.return_value = mock.Mock(
            status_code=200,
            json=lambda: invalid_response
        )

        result = self.service.fetch_and_store_prices()

        # Should only insert the valid record
        assert result["inserted"] == 1
        assert MetalPrice.objects.count() == 1
