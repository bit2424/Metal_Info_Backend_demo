"""
MetalNews model for storing metal industry news articles.
"""
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from safedelete import SOFT_DELETE
from safedelete.models import SafeDeleteModel

from shared.models import UUIDTimeStampedAbstractModel


class MetalNews(UUIDTimeStampedAbstractModel, SafeDeleteModel):
    """
    Stores metal industry news articles fetched from RSS feeds.
    Each record represents a single news article with full-text search support.
    """

    _safedelete_policy = SOFT_DELETE

    # Article information
    title = models.CharField(
        max_length=500,
        db_index=True,
        help_text="Article title"
    )
    """ Article title """

    description = models.TextField(
        blank=True,
        help_text="Article description or summary"
    )
    """ Article description or summary """

    url = models.URLField(
        max_length=1000,
        unique=True,
        help_text="Article URL (unique to prevent duplicates)"
    )
    """ Article URL (unique to prevent duplicates) """

    source = models.CharField(
        max_length=200,
        db_index=True,
        help_text="News source name"
    )
    """ News source name """

    published_at = models.DateTimeField(
        db_index=True,
        help_text="Article publication timestamp"
    )
    """ Article publication timestamp """

    # Full-text search vector
    search_vector = SearchVectorField(
        null=True,
        blank=True,
        help_text="Full-text search vector for PostgreSQL search"
    )
    """ Full-text search vector for PostgreSQL search """

    # Keywords relationship (many-to-many through NewsKeyword)
    keywords = models.ManyToManyField(
        "Keyword",
        through="NewsKeyword",
        related_name="news_articles",
        help_text="Keywords associated with this news article"
    )
    """ Keywords associated with this news article """

    class Meta:
        db_table = "metal_news"
        verbose_name = "Metal News"
        verbose_name_plural = "Metal News"
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["source"]),
            models.Index(fields=["-published_at"]),
            GinIndex(fields=["search_vector"]),  # Fast full-text search
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["url"],
                name="unique_news_url"
            )
        ]

    def __str__(self):
        return f"{self.title} ({self.source})"

    @property
    def short_description(self) -> str:
        """Return a shortened version of the description."""
        if len(self.description) <= 100:
            return self.description
        return self.description[:97] + "..."
