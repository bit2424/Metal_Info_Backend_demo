"""
Business logic services for Metal Prices.
"""
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from metal_prices.models import MetalPrice

logger = logging.getLogger(__name__)


class ExternalAPIError(Exception):
    """Exception raised for external API errors."""
    pass


class MetalPriceService:
    """
    Service class for metal price operations.
    """

    def __init__(self):
        self.config = settings.METAL_PRICES_CONFIG
        self.api_url = self.config["API_URL"]
        self.api_timeout = self.config["API_TIMEOUT"]
        self.supported_metals = self.config["SUPPORTED_METALS"]

    def fetch_and_store_prices(self, metals: list[str] | None = None) -> dict[str, Any]:
        """
        Fetch metal prices from external API and store in database.

        Args:
            metals: Optional list of metal symbols to fetch

        Returns:
            Dict with success status, message, and inserted count

        Raises:
            ExternalAPIError: If the external API request fails
        """
        metals = metals or self.supported_metals

        # Build query parameters
        params = [("metals", metal) for metal in metals]

        logger.info(f"Fetching prices for {len(metals)} metals from external API")

        try:
            response = requests.get(
                self.api_url,
                params=params,
                timeout=self.api_timeout
            )
            response.raise_for_status()
            data = response.json()

        except requests.RequestException as e:
            logger.error(f"External API request failed: {e}")
            raise ExternalAPIError(f"Failed to fetch prices: {e}") from e

        if not isinstance(data, list):
            raise ExternalAPIError("Invalid API response format - expected array")

        return self._process_and_store(data)

    @transaction.atomic
    def _process_and_store(self, data: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Process API response and store in database.

        Args:
            data: List of metal price data from external API

        Returns:
            Dict with processing results
        """
        fetched_at = timezone.now()
        prices_to_create = []
        summaries = []

        for metal_data in data:
            material = metal_data.get("material")
            if not material:
                logger.warning(f"Skipping invalid metal data: {metal_data}")
                continue

            # Get latest price from prices array
            prices = metal_data.get("prices", [])
            latest_price = (
                prices[-1]["priceNormalised"]
                if prices
                else metal_data.get("chartIndicator", 0)
            )

            # Convert lastDate timestamp from milliseconds to datetime
            last_date_ts = metal_data.get("lastDate")
            last_date = (
                datetime.fromtimestamp(last_date_ts / 1000, tz=timezone.utc)
                if last_date_ts
                else None
            )

            metal_price = MetalPrice(
                symbol=material,
                name=material,
                price_usd=Decimal(str(latest_price)),
                unit="normalized",
                indicator_one=Decimal(str(metal_data.get("indicatorOne", 0))),
                indicator_two=Decimal(str(metal_data.get("indicatorTwo", 0))),
                indicator_three=Decimal(str(metal_data.get("indicatorThree", 0))),
                chart_indicator=Decimal(str(metal_data.get("chartIndicator", 0))),
                last_date=last_date,
                price_history=prices,
                fetched_at=fetched_at,
            )
            prices_to_create.append(metal_price)

            summaries.append({
                "symbol": material,
                "chart_indicator": metal_price.chart_indicator,
                "indicator_one": metal_price.indicator_one,
                "price_history_count": len(prices),
            })

        # Bulk create all prices
        MetalPrice.objects.bulk_create(prices_to_create)

        logger.info(f"Successfully stored {len(prices_to_create)} metal prices")

        return {
            "success": True,
            "message": f"Fetched and stored {len(prices_to_create)} metal prices",
            "inserted": len(prices_to_create),
            "fetched_at": fetched_at,
            "prices": summaries,
        }

    def get_latest_prices(self, symbols: list[str] | None = None) -> list[MetalPrice]:
        """
        Get the latest batch of metal prices.

        Args:
            symbols: Optional list of symbols to filter

        Returns:
            List of MetalPrice objects
        """
        from django.db.models import Max

        latest_fetch = MetalPrice.objects.aggregate(
            latest=Max("fetched_at")
        )["latest"]

        if not latest_fetch:
            return []

        queryset = MetalPrice.objects.filter(fetched_at=latest_fetch)

        if symbols:
            queryset = queryset.filter(symbol__in=symbols)

        return list(queryset.order_by("symbol"))

    def get_price_by_symbol(self, symbol: str) -> MetalPrice | None:
        """
        Get the latest price for a specific metal symbol.

        Args:
            symbol: Metal symbol to fetch

        Returns:
            MetalPrice object or None if not found
        """
        from django.db.models import Max

        latest_fetch = MetalPrice.objects.aggregate(
            latest=Max("fetched_at")
        )["latest"]

        if not latest_fetch:
            return None

        try:
            return MetalPrice.objects.get(
                symbol=symbol,
                fetched_at=latest_fetch
            )
        except MetalPrice.DoesNotExist:
            return None
