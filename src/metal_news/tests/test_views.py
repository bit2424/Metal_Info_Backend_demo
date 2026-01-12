"""
Tests for Metal News API views.
"""
import pytest
from unittest.mock import patch, Mock
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from metal_news.models import MetalNews


@pytest.fixture
def api_client():
    """API client fixture."""
    return APIClient()


@pytest.mark.django_db
class TestMetalNewsListView:
    """Test cases for MetalNewsListView."""

    def test_list_news_empty(self, api_client):
        """Test listing news when database is empty."""
        url = reverse("metal_news:metal-news-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["count"] == 0

    def test_list_news_with_data(self, api_client):
        """Test listing news with data."""
        now = timezone.now()

        # Create test news
        for i in range(3):
            MetalNews.objects.create(
                title=f"News {i}",
                description=f"Description {i}",
                url=f"https://example.com/news-{i}",
                source="Test Source",
                published_at=now - timezone.timedelta(hours=i),
            )

        url = reverse("metal_news:metal-news-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["count"] == 3

    def test_filter_by_source(self, api_client):
        """Test filtering news by source."""
        now = timezone.now()

        MetalNews.objects.create(
            title="News A",
            url="https://example.com/a",
            source="Source A",
            published_at=now,
        )

        MetalNews.objects.create(
            title="News B",
            url="https://example.com/b",
            source="Source B",
            published_at=now,
        )

        url = reverse("metal_news:metal-news-list")
        response = api_client.get(url, {"source": "Source A"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1


@pytest.mark.django_db
class TestMetalNewsDetailView:
    """Test cases for MetalNewsDetailView."""

    def test_retrieve_news(self, api_client):
        """Test retrieving a specific news article."""
        news = MetalNews.objects.create(
            title="Test News",
            description="Test description",
            url="https://example.com/test",
            source="Test Source",
            published_at=timezone.now(),
        )

        url = reverse("metal_news:metal-news-detail", kwargs={"uuid": news.uuid})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["data"]["title"] == "Test News"

    def test_retrieve_nonexistent_news(self, api_client):
        """Test retrieving a non-existent news article."""
        import uuid
        url = reverse("metal_news:metal-news-detail", kwargs={"uuid": uuid.uuid4()})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestMetalNewsSearchView:
    """Test cases for MetalNewsSearchView."""

    def test_search_without_query(self, api_client):
        """Test search without query parameter."""
        url = reverse("metal_news:metal-news-search")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False

    def test_search_with_query(self, api_client):
        """Test search with query parameter."""
        # Create test news with search vector
        news = MetalNews.objects.create(
            title="Copper prices surge",
            description="Copper market sees significant growth",
            url="https://example.com/copper",
            source="Metal News",
            published_at=timezone.now(),
        )

        # Update search vector (normally done by signal)
        from django.contrib.postgres.search import SearchVector
        MetalNews.objects.filter(pk=news.pk).update(
            search_vector=(
                SearchVector("title", weight="A") +
                SearchVector("description", weight="B") +
                SearchVector("source", weight="C")
            )
        )

        url = reverse("metal_news:metal-news-search")
        response = api_client.get(url, {"q": "copper"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["query"] == "copper"


@pytest.mark.django_db
class TestFetchMetalNewsView:
    """Test cases for FetchMetalNewsView."""

    @patch("metal_news.api.v1.views.NewsService")
    def test_fetch_success(self, mock_service_class, api_client):
        """Test successful news fetch."""
        # Mock service
        mock_service = Mock()
        mock_service.fetch_and_store_news.return_value = {
            "success": True,
            "message": "Fetched 5 articles",
            "inserted": 5,
            "skipped": 0,
            "total_fetched": 5,
        }
        mock_service_class.return_value = mock_service

        url = reverse("metal_news:metal-news-fetch")
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["inserted"] == 5

    @patch("metal_news.api.v1.views.NewsService")
    def test_fetch_error(self, mock_service_class, api_client):
        """Test fetch with error."""
        from metal_news.api.v1.services import RSSFeedError

        # Mock service to raise error
        mock_service = Mock()
        mock_service.fetch_and_store_news.side_effect = RSSFeedError("Feed error")
        mock_service_class.return_value = mock_service

        url = reverse("metal_news:metal-news-fetch")
        response = api_client.post(url)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data["success"] is False
