"""
Tests for keyword-related API views.
"""
import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from metal_news.models import Keyword, MetalNews, NewsKeyword


@pytest.fixture
def api_client():
    """API client fixture."""
    return APIClient()


@pytest.mark.django_db
class TestMetalNewsListViewWithKeywords:
    """Test cases for filtering news by keywords."""

    def test_filter_by_keyword_name(self, api_client):
        """Test filtering news by keyword name."""
        copper = Keyword.objects.create(name="Copper")
        steel = Keyword.objects.create(name="Steel")

        news1 = MetalNews.objects.create(
            title="Copper Market Update",
            url="https://example.com/copper",
            source="Metal News",
            published_at=timezone.now(),
        )

        news2 = MetalNews.objects.create(
            title="Steel Industry Report",
            url="https://example.com/steel",
            source="Metal News",
            published_at=timezone.now(),
        )

        NewsKeyword.objects.create(
            news=news1,
            keyword=copper,
            keyword_type=NewsKeyword.KeywordType.RELATED_METAL
        )

        NewsKeyword.objects.create(
            news=news2,
            keyword=steel,
            keyword_type=NewsKeyword.KeywordType.RELATED_METAL
        )

        url = reverse("metal_news:metal-news-list")
        response = api_client.get(url, {"keyword": "Copper"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["title"] == "Copper Market Update"

    def test_filter_by_keyword_slug(self, api_client):
        """Test filtering news by keyword slug."""
        keyword = Keyword.objects.create(name="Steel Industry")

        news = MetalNews.objects.create(
            title="Steel News",
            url="https://example.com/steel",
            source="Test",
            published_at=timezone.now(),
        )

        NewsKeyword.objects.create(
            news=news,
            keyword=keyword,
            keyword_type=NewsKeyword.KeywordType.INDUSTRY
        )

        url = reverse("metal_news:metal-news-list")
        response = api_client.get(url, {"keyword": "steel-industry"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_filter_by_keyword_type(self, api_client):
        """Test filtering news by keyword type."""
        copper = Keyword.objects.create(name="Copper")
        china = Keyword.objects.create(name="China")

        news = MetalNews.objects.create(
            title="China Copper Market",
            url="https://example.com/china-copper",
            source="Test",
            published_at=timezone.now(),
        )

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

        url = reverse("metal_news:metal-news-list")
        response = api_client.get(url, {"keyword_type": "country"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_filter_by_keyword_and_type(self, api_client):
        """Test filtering by both keyword and type."""
        copper = Keyword.objects.create(name="Copper")

        news1 = MetalNews.objects.create(
            title="Copper Market",
            url="https://example.com/copper1",
            source="Test",
            published_at=timezone.now(),
        )

        news2 = MetalNews.objects.create(
            title="Copper Analysis",
            url="https://example.com/copper2",
            source="Test",
            published_at=timezone.now(),
        )

        NewsKeyword.objects.create(
            news=news1,
            keyword=copper,
            keyword_type=NewsKeyword.KeywordType.RELATED_METAL
        )

        NewsKeyword.objects.create(
            news=news2,
            keyword=copper,
            keyword_type=NewsKeyword.KeywordType.TOPIC
        )

        url = reverse("metal_news:metal-news-list")
        response = api_client.get(url, {
            "keyword": "Copper",
            "keyword_type": "related_metal"
        })

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["title"] == "Copper Market"

    def test_keywords_in_response(self, api_client):
        """Test that keywords are included in the response."""
        copper = Keyword.objects.create(name="Copper")
        china = Keyword.objects.create(name="China")

        news = MetalNews.objects.create(
            title="China Copper Market",
            url="https://example.com/china-copper",
            source="Test",
            published_at=timezone.now(),
        )

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

        url = reverse("metal_news:metal-news-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "keywordsByType" in response.data["results"][0]

        keywords_by_type = response.data["results"][0]["keywordsByType"]
        assert "related_metal" in keywords_by_type
        assert "country" in keywords_by_type
        assert len(keywords_by_type["related_metal"]) == 1
        assert keywords_by_type["related_metal"][0]["name"] == "Copper"


@pytest.mark.django_db
class TestKeywordListView:
    """Test cases for KeywordListView."""

    def test_list_all_keywords(self, api_client):
        """Test listing all keywords."""
        Keyword.objects.create(name="Copper")
        Keyword.objects.create(name="Steel")
        Keyword.objects.create(name="Aluminum")

        url = reverse("metal_news:keywords-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["count"] == 3

    def test_filter_keywords_by_type(self, api_client):
        """Test filtering keywords by type."""
        copper = Keyword.objects.create(name="Copper")
        steel = Keyword.objects.create(name="Steel")
        china = Keyword.objects.create(name="China")

        news = MetalNews.objects.create(
            title="Test News",
            url="https://example.com/test",
            source="Test",
            published_at=timezone.now(),
        )

        NewsKeyword.objects.create(
            news=news,
            keyword=copper,
            keyword_type=NewsKeyword.KeywordType.RELATED_METAL
        )

        NewsKeyword.objects.create(
            news=news,
            keyword=steel,
            keyword_type=NewsKeyword.KeywordType.RELATED_METAL
        )

        NewsKeyword.objects.create(
            news=news,
            keyword=china,
            keyword_type=NewsKeyword.KeywordType.COUNTRY
        )

        url = reverse("metal_news:keywords-list")
        response = api_client.get(url, {"type": "related_metal"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

    def test_search_keywords(self, api_client):
        """Test searching keywords by name."""
        Keyword.objects.create(name="Copper")
        Keyword.objects.create(name="Copper Alloy")
        Keyword.objects.create(name="Steel")

        url = reverse("metal_news:keywords-list")
        response = api_client.get(url, {"search": "copper"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2
