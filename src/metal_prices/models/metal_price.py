"""
MetalPrice model for storing metal price snapshots.
"""
from django.db import models
from safedelete import SOFT_DELETE
from safedelete.models import SafeDeleteModel

from shared.models import UUIDTimeStampedAbstractModel


class MetalPrice(UUIDTimeStampedAbstractModel, SafeDeleteModel):
    """
    Stores metal price snapshots fetched from external API.
    Each record represents a single metal's price data at a specific fetch time.
    """

    _safedelete_policy = SOFT_DELETE

    # Basic metal information
    symbol = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Metal identifier/symbol"
    )
    """ Metal identifier/symbol """

    name = models.CharField(
        max_length=100,
        help_text="Metal display name"
    )
    """ Metal display name """

    # Price information
    price_usd = models.DecimalField(
        max_digits=20,
        decimal_places=10,
        help_text="Latest normalized price value"
    )
    """ Latest normalized price value """

    unit = models.CharField(
        max_length=50,
        default="normalized",
        help_text="Price unit type"
    )
    """ Price unit type """

    # Indicators
    indicator_one = models.DecimalField(
        max_digits=20,
        decimal_places=10,
        null=True,
        blank=True,
        help_text="First indicator value"
    )
    """ First indicator value """

    indicator_two = models.DecimalField(
        max_digits=20,
        decimal_places=10,
        null=True,
        blank=True,
        help_text="Second indicator value"
    )
    """ Second indicator value """

    indicator_three = models.DecimalField(
        max_digits=20,
        decimal_places=10,
        null=True,
        blank=True,
        help_text="Third indicator value"
    )
    """ Third indicator value """

    chart_indicator = models.DecimalField(
        max_digits=20,
        decimal_places=10,
        null=True,
        blank=True,
        help_text="Chart indicator value"
    )
    """ Chart indicator value """

    # Timestamp information
    last_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last date from external API"
    )
    """ Last date from external API """

    fetched_at = models.DateTimeField(
        db_index=True,
        help_text="Timestamp when data was fetched from API"
    )
    """ Timestamp when data was fetched from API """

    # Historical data
    price_history = models.JSONField(
        null=True,
        blank=True,
        help_text="Historical price data as JSON array"
    )
    """ Historical price data as JSON array """

    class Meta:
        db_table = "metal_prices"
        verbose_name = "Metal Price"
        verbose_name_plural = "Metal Prices"
        ordering = ["-fetched_at", "symbol"]
        indexes = [
            models.Index(fields=["symbol"]),
            models.Index(fields=["-fetched_at"]),
        ]

    def __str__(self):
        return f"{self.symbol} - {self.price_usd} ({self.fetched_at})"

    @property
    def price_history_count(self) -> int:
        """Return the count of historical price points."""
        if self.price_history and isinstance(self.price_history, list):
            return len(self.price_history)
        return 0
