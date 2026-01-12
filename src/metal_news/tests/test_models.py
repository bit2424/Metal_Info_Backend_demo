"""
Tests for MetalNews model.
"""
import pytest
from django.utils import timezone

from metal_news.models import MetalNews


@pytest.mark.django_db
class TestMetalNewsModel:
    """Test cases for MetalNews model."""

    def test_create_metal_news(self):
        """Test creating a MetalNews instance."""
        news = MetalNews.objects.create(
            title="Test News Article",
            description="This is a test news article about metal prices.",
            url="https://example.com/test-article",
            source="Test Source",
            published_at=timezone.now(),
        )

        assert news.uuid is not None
        assert news.title == "Test News Article"
        assert news.source == "Test Source"
        assert str(news) == "Test News Article (Test Source)"

    def test_unique_url_constraint(self):
        """Test that URL must be unique."""
        MetalNews.objects.create(
            title="First Article",
            description="First description",
            url="https://example.com/duplicate-url",
            source="Source A",
            published_at=timezone.now(),
        )

        with pytest.raises(Exception):  # IntegrityError
            MetalNews.objects.create(
                title="Second Article",
                description="Second description",
                url="https://example.com/duplicate-url",
                source="Source B",
                published_at=timezone.now(),
            )

    def test_short_description_property(self):
        """Test short_description property."""
        # Short description (less than 100 chars)
        news1 = MetalNews.objects.create(
            title="Short",
            description="This is short.",
            url="https://example.com/short",
            source="Test",
            published_at=timezone.now(),
        )
        assert news1.short_description == "This is short."

        # Long description (more than 100 chars)
        long_desc = "A" * 150
        news2 = MetalNews.objects.create(
            title="Long",
            description=long_desc,
            url="https://example.com/long",
            source="Test",
            published_at=timezone.now(),
        )
        assert len(news2.short_description) == 100
        assert news2.short_description.endswith("...")

    def test_ordering(self):
        """Test that news are ordered by published_at descending."""
        now = timezone.now()

        news1 = MetalNews.objects.create(
            title="Old News",
            url="https://example.com/old",
            source="Test",
            published_at=now - timezone.timedelta(days=2),
        )

        news2 = MetalNews.objects.create(
            title="New News",
            url="https://example.com/new",
            source="Test",
            published_at=now,
        )

        news_list = list(MetalNews.objects.all())
        assert news_list[0] == news2  # Newest first
        assert news_list[1] == news1
