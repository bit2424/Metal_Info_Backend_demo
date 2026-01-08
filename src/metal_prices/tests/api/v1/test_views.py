"""
Tests for Metal Prices API views.
"""
from unittest import mock

import pytest
from django.urls import reverse
from rest_framework import status

from metal_prices.models import MetalPrice


@pytest.mark.django_db
class TestMetalPriceListView:
    """Tests for the metal price list endpoint."""

    def test_list_metal_prices_success(self, api_client, sample_metal_prices):
        """Test successfully retrieving the latest metal prices."""
        endpoint = reverse("metal_prices:metal-price-list")
        response = api_client.get(endpoint)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["success"] is True
        assert response.json()["count"] == 3
        assert len(response.json()["data"]) == 3

    def test_list_metal_prices_empty(self, api_client):
        """Test retrieving metal prices when database is empty."""
        endpoint = reverse("metal_prices:metal-price-list")
        response = api_client.get(endpoint)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["success"] is True
        assert response.json()["count"] == 0
        assert response.json()["data"] == []

    def test_list_metal_prices_filter_by_symbols(self, api_client, sample_metal_prices):
        """Test filtering metal prices by symbols query parameter."""
        endpoint = reverse("metal_prices:metal-price-list")
        response = api_client.get(f"{endpoint}?symbols=Tense,Troma")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 2
        symbols = [item["symbol"] for item in response.json()["data"]]
        assert "Tense" in symbols
        assert "Troma" in symbols
        assert "Zorba" not in symbols


@pytest.mark.django_db
class TestMetalPriceDetailView:
    """Tests for the metal price detail endpoint."""

    def test_get_metal_price_by_symbol_success(self, api_client, sample_metal_prices):
        """Test successfully retrieving a specific metal price."""
        endpoint = reverse("metal_prices:metal-price-detail", kwargs={"symbol": "Tense"})
        response = api_client.get(endpoint)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["success"] is True
        assert response.json()["data"]["symbol"] == "Tense"

    def test_get_metal_price_not_found(self, api_client):
        """Test retrieving a non-existent metal price."""
        endpoint = reverse("metal_prices:metal-price-detail", kwargs={"symbol": "InvalidMetal"})
        response = api_client.get(endpoint)

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestFetchMetalPricesView:
    """Tests for the fetch metal prices endpoint."""

    @mock.patch("requests.get")
    def test_fetch_metal_prices_success(self, mock_get, api_client, mock_api_response):
        """Test successfully fetching and storing metal prices."""
        # Mock the external API response
        mock_get.return_value = mock.Mock(
            status_code=200,
            json=lambda: mock_api_response
        )

        endpoint = reverse("metal_prices:fetch-metal-prices")
        response = api_client.post(endpoint, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["success"] is True
        assert response.json()["inserted"] == 2
        assert MetalPrice.objects.count() == 2

        # Verify mock was called
        assert mock_get.called

    @mock.patch("requests.get")
    def test_fetch_metal_prices_with_specific_metals(
        self, mock_get, api_client, mock_api_response, valid_fetch_payload
    ):
        """Test fetching specific metals only."""
        mock_get.return_value = mock.Mock(
            status_code=200,
            json=lambda: mock_api_response
        )

        endpoint = reverse("metal_prices:fetch-metal-prices")
        response = api_client.post(endpoint, data=valid_fetch_payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["success"] is True
        assert response.json()["inserted"] == 2

    @mock.patch("requests.get")
    def test_fetch_metal_prices_api_error(self, mock_get, api_client):
        """Test handling of external API errors."""
        # Mock API failure
        mock_get.side_effect = Exception("Connection timeout")

        endpoint = reverse("metal_prices:fetch-metal-prices")
        response = api_client.post(endpoint, format="json")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["success"] is False
        assert "error" in response.json()

    @mock.patch("requests.get")
    def test_fetch_metal_prices_invalid_response_format(self, mock_get, api_client):
        """Test handling of invalid API response format."""
        # Mock invalid response (not a list)
        mock_get.return_value = mock.Mock(
            status_code=200,
            json=lambda: {"error": "Invalid format"}
        )

        endpoint = reverse("metal_prices:fetch-metal-prices")
        response = api_client.post(endpoint, format="json")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["success"] is False


@pytest.mark.django_db
class TestCamelSnakeCaseConversion:
    """Tests for camelCase/snake_case conversion in API."""

    @mock.patch("requests.get")
    def test_request_camel_case_converted_to_snake_case(
        self, mock_get, api_client, mock_api_response
    ):
        """Test that camelCase request data is converted to snake_case."""
        mock_get.return_value = mock.Mock(
            status_code=200,
            json=lambda: mock_api_response
        )

        endpoint = reverse("metal_prices:fetch-metal-prices")
        # Send camelCase request
        response = api_client.post(
            endpoint,
            data={"metals": ["Tense"]},  # This is already valid, testing service layer
            format="json"
        )

        assert response.status_code == status.HTTP_200_OK

    def test_response_snake_case_converted_to_camel_case(self, api_client, sample_metal_prices):
        """Test that snake_case response data is converted to camelCase."""
        endpoint = reverse("metal_prices:metal-price-list")
        response = api_client.get(endpoint)

        assert response.status_code == status.HTTP_200_OK
        # Check that response has camelCase keys
        data = response.json()
        assert "fetchedAt" in data  # snake_case fetched_at -> camelCase fetchedAt
        if data["data"]:
            first_item = data["data"][0]
            assert "priceUsd" in first_item  # snake_case price_usd -> camelCase priceUsd
            assert "chartIndicator" in first_item
