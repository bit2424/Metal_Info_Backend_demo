"""
Tests for Keyword models and functionality.
"""
import pytest
from django.utils import timezone

from metal_news.models import Keyword, MetalNews, NewsKeyword


@pytest.mark.django_db
class TestKeywordModel:
    """Test cases for Keyword model."""

    def test_create_keyword(self):
        """Test creating a Keyword instance."""
        keyword = Keyword.objects.create(name="Copper")

        assert keyword.uuid is not None
        assert keyword.name == "Copper"
        assert keyword.slug == "copper"
        assert str(keyword) == "Copper"

    def test_keyword_slug_auto_generation(self):
        """Test that slug is automatically generated from name."""
        keyword = Keyword.objects.create(name="Steel Industry")

        assert keyword.slug == "steel-industry"

    def test_keyword_unique_name(self):
        """Test that keyword names must be unique."""
        Keyword.objects.create(name="Aluminum")

        with pytest.raises(Exception):  # IntegrityError
            Keyword.objects.create(name="Aluminum")


@pytest.mark.django_db
class TestNewsKeywordModel:
    """Test cases for NewsKeyword model."""

    def test_create_news_keyword_association(self):
        """Test creating a NewsKeyword association."""
        news = MetalNews.objects.create(
            title="Test News",
            url="https://example.com/test",
            source="Test Source",
            published_at=timezone.now(),
        )

        keyword = Keyword.objects.create(name="Copper")

        news_keyword = NewsKeyword.objects.create(
            news=news,
            keyword=keyword,
            keyword_type=NewsKeyword.KeywordType.RELATED_METAL
        )

        assert news_keyword.uuid is not None
        assert news_keyword.news == news
        assert news_keyword.keyword == keyword
        assert news_keyword.keyword_type == NewsKeyword.KeywordType.RELATED_METAL

    def test_keyword_type_choices(self):
        """Test that all keyword type choices are available."""
        types = NewsKeyword.KeywordType.choices

        assert len(types) == 7
        assert ("topic", "Topic") in types
        assert ("country", "Country") in types
        assert ("related_metal", "Related Metal") in types
        assert ("industry", "Industry") in types
        assert ("company", "Company") in types
        assert ("region", "Region") in types
        assert ("other", "Other") in types

    def test_unique_together_constraint(self):
        """Test that news + keyword + keyword_type must be unique."""
        news = MetalNews.objects.create(
            title="Test News",
            url="https://example.com/test",
            source="Test Source",
            published_at=timezone.now(),
        )

        keyword = Keyword.objects.create(name="China")

        NewsKeyword.objects.create(
            news=news,
            keyword=keyword,
            keyword_type=NewsKeyword.KeywordType.COUNTRY
        )

        # Same news + keyword + type should fail
        with pytest.raises(Exception):  # IntegrityError
            NewsKeyword.objects.create(
                news=news,
                keyword=keyword,
                keyword_type=NewsKeyword.KeywordType.COUNTRY
            )

    def test_same_keyword_different_types(self):
        """Test that the same keyword can have different types."""
        news = MetalNews.objects.create(
            title="Test News",
            url="https://example.com/test",
            source="Test Source",
            published_at=timezone.now(),
        )

        keyword = Keyword.objects.create(name="Steel")

        # Same keyword as related_metal
        nk1 = NewsKeyword.objects.create(
            news=news,
            keyword=keyword,
            keyword_type=NewsKeyword.KeywordType.RELATED_METAL
        )

        # Same keyword as topic
        nk2 = NewsKeyword.objects.create(
            news=news,
            keyword=keyword,
            keyword_type=NewsKeyword.KeywordType.TOPIC
        )

        assert nk1.keyword == nk2.keyword
        assert nk1.keyword_type != nk2.keyword_type


@pytest.mark.django_db
class TestNewsWithKeywords:
    """Test cases for news articles with keywords."""

    def test_news_keywords_relationship(self):
        """Test many-to-many relationship between news and keywords."""
        news = MetalNews.objects.create(
            title="Copper Market Analysis",
            url="https://example.com/copper",
            source="Metal News",
            published_at=timezone.now(),
        )

        copper = Keyword.objects.create(name="Copper")
        china = Keyword.objects.create(name="China")
        mining = Keyword.objects.create(name="Mining")

        NewsKeyword.objects.create(
            news=news,
            keyword=copper,
            keyword_type=NewsKeyword.KeywordType.RELATED_METAL
        )

        NewsKeyword.objects.create(
            news=news,
            keyword=china,
            keyword_type=NewsKeyword.KeywordType.COUNTRY
        )

        NewsKeyword.objects.create(
            news=news,
            keyword=mining,
            keyword_type=NewsKeyword.KeywordType.INDUSTRY
        )

        # Test access through relationship
        assert news.keywords.count() == 3
        assert copper in news.keywords.all()
        assert china in news.keywords.all()
        assert mining in news.keywords.all()

    def test_keywords_grouped_by_type(self):
        """Test grouping keywords by type."""
        news = MetalNews.objects.create(
            title="Test News",
            url="https://example.com/test",
            source="Test Source",
            published_at=timezone.now(),
        )

        copper = Keyword.objects.create(name="Copper")
        aluminum = Keyword.objects.create(name="Aluminum")
        china = Keyword.objects.create(name="China")

        NewsKeyword.objects.create(
            news=news,
            keyword=copper,
            keyword_type=NewsKeyword.KeywordType.RELATED_METAL
        )

        NewsKeyword.objects.create(
            news=news,
            keyword=aluminum,
            keyword_type=NewsKeyword.KeywordType.RELATED_METAL
        )

        NewsKeyword.objects.create(
            news=news,
            keyword=china,
            keyword_type=NewsKeyword.KeywordType.COUNTRY
        )

        # Group by type
        metals = news.news_keywords.filter(
            keyword_type=NewsKeyword.KeywordType.RELATED_METAL
        )
        countries = news.news_keywords.filter(
            keyword_type=NewsKeyword.KeywordType.COUNTRY
        )

        assert metals.count() == 2
        assert countries.count() == 1

    def test_filter_news_by_keyword(self):
        """Test filtering news articles by keyword."""
        copper_keyword = Keyword.objects.create(name="Copper")
        steel_keyword = Keyword.objects.create(name="Steel")

        news1 = MetalNews.objects.create(
            title="Copper News",
            url="https://example.com/copper-news",
            source="Test",
            published_at=timezone.now(),
        )

        news2 = MetalNews.objects.create(
            title="Steel News",
            url="https://example.com/steel-news",
            source="Test",
            published_at=timezone.now(),
        )

        NewsKeyword.objects.create(
            news=news1,
            keyword=copper_keyword,
            keyword_type=NewsKeyword.KeywordType.RELATED_METAL
        )

        NewsKeyword.objects.create(
            news=news2,
            keyword=steel_keyword,
            keyword_type=NewsKeyword.KeywordType.RELATED_METAL
        )

        # Filter by keyword
        copper_news = MetalNews.objects.filter(
            news_keywords__keyword=copper_keyword
        )

        assert copper_news.count() == 1
        assert copper_news.first() == news1
