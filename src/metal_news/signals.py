"""
Signal handlers for Metal News.
"""
from django.contrib.postgres.search import SearchVector
from django.db.models.signals import post_save
from django.dispatch import receiver

from metal_news.models import MetalNews


@receiver(post_save, sender=MetalNews)
def update_search_vector(sender, instance, **kwargs):
    """
    Automatically update search_vector when a MetalNews instance is saved.

    This ensures the full-text search index is always up to date.
    """
    # Avoid infinite recursion by checking if we're already updating
    if kwargs.get("update_fields") and "search_vector" in kwargs["update_fields"]:
        return

    # Update search vector with weighted fields
    MetalNews.objects.filter(pk=instance.pk).update(
        search_vector=(
            SearchVector("title", weight="A") +  # Highest weight for title
            SearchVector("description", weight="B") +  # Medium weight for description
            SearchVector("source", weight="C")  # Lower weight for source
        )
    )
