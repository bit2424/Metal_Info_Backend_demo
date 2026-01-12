"""
Keyword models for categorizing and tagging news articles.
"""
from django.db import models

from shared.models import UUIDTimeStampedAbstractModel


class Keyword(UUIDTimeStampedAbstractModel):
    """
    Represents a keyword that can be associated with news articles.
    Keywords are reusable across multiple articles.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Keyword name (e.g., 'copper', 'China', 'mining')"
    )
    """ Keyword name """

    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text="URL-friendly version of the keyword"
    )
    """ URL-friendly slug """

    class Meta:
        db_table = "keywords"
        verbose_name = "Keyword"
        verbose_name_plural = "Keywords"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not provided."""
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class NewsKeyword(UUIDTimeStampedAbstractModel):
    """
    Intermediate model linking news articles to keywords with a type classification.
    Allows the same keyword to have different types in different contexts.
    """

    class KeywordType(models.TextChoices):
        """Types of keywords for categorization."""
        TOPIC = "topic", "Topic"
        COUNTRY = "country", "Country"
        RELATED_METAL = "related_metal", "Related Metal"
        INDUSTRY = "industry", "Industry"
        COMPANY = "company", "Company"
        REGION = "region", "Region"
        OTHER = "other", "Other"

    news = models.ForeignKey(
        "MetalNews",
        on_delete=models.CASCADE,
        related_name="news_keywords",
        help_text="News article"
    )
    """ News article """

    keyword = models.ForeignKey(
        Keyword,
        on_delete=models.CASCADE,
        related_name="news_keywords",
        help_text="Keyword"
    )
    """ Keyword """

    keyword_type = models.CharField(
        max_length=20,
        choices=KeywordType.choices,
        default=KeywordType.OTHER,
        db_index=True,
        help_text="Type/category of the keyword"
    )
    """ Type/category of the keyword """

    class Meta:
        db_table = "news_keywords"
        verbose_name = "News Keyword"
        verbose_name_plural = "News Keywords"
        ordering = ["keyword_type", "keyword__name"]
        unique_together = [["news", "keyword", "keyword_type"]]
        indexes = [
            models.Index(fields=["news", "keyword_type"]),
            models.Index(fields=["keyword", "keyword_type"]),
        ]

    def __str__(self):
        return f"{self.news.title[:50]} - {self.keyword.name} ({self.keyword_type})"
