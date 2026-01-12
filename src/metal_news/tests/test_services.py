"""
Tests for NewsService.
"""
import pytest
from unittest.mock import Mock, patch
from django.utils import timezone

from metal_news.api.v1.services import NewsService, RSSFeedError
from metal_news.models import MetalNews


@pytest.mark.django_db
class TestNewsService:
    """Test cases for NewsService."""

    def test_init(self):
        """Test NewsService initialization."""
        service = NewsService()
        assert service.rss_base_url == "https://news.google.com/rss/search"
        assert len(service.search_terms) > 0

    def test_process_and_store_new_articles(self, sample_article_data):
        """Test storing new articles."""
        service = NewsService()
        articles = [sample_article_data]

        result = service._process_and_store(articles)

        assert result["success"] is True
        assert result["inserted"] == 1
        assert result["skipped"] == 0
        assert MetalNews.objects.count() == 1

    def test_process_and_store_duplicate_articles(self, sample_article_data):
        """Test that duplicate articles are skipped."""
        service = NewsService()

        # Store first article
        result1 = service._process_and_store([sample_article_data])
        assert result1["inserted"] == 1

        # Try to store same article again
        result2 = service._process_and_store([sample_article_data])
        assert result2["inserted"] == 0
        assert result2["skipped"] == 1
        assert MetalNews.objects.count() == 1  # Still only 1

    def test_get_latest_news(self):
        """Test getting latest news."""
        service = NewsService()
        now = timezone.now()

        # Create multiple news articles
        for i in range(5):
            MetalNews.objects.create(
                title=f"News {i}",
                url=f"https://example.com/news-{i}",
                source="Test",
                published_at=now - timezone.timedelta(days=i),
            )

        latest = service.get_latest_news(limit=3)
        assert len(latest) == 3
        assert latest[0].title == "News 0"  # Most recent

    def test_get_news_by_source(self):
        """Test filtering news by source."""
        service = NewsService()
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

        results = service.get_news_by_source("Source A")
        assert results.count() == 1
        assert results.first().source == "Source A"

    @pytest.mark.django_db
    def test_search_news_empty_query(self):
        """Test search with empty query returns nothing."""
        service = NewsService()

        results = service.search_news("")
        assert results.count() == 0

    @patch("metal_news.api.v1.services.requests.get")
    def test_fetch_rss_feed_request_error(self, mock_get):
        """Test RSS feed fetch with request error."""
        service = NewsService()
        mock_get.side_effect = Exception("Network error")

        with pytest.raises(RSSFeedError):
            service._fetch_rss_feed("test query")

    @patch("metal_news.api.v1.services.requests.get")
    @patch("metal_news.api.v1.services.feedparser.parse")
    def test_fetch_rss_feed_success(self, mock_parse, mock_get):
        """Test successful RSS feed fetch."""
        service = NewsService()

        # Mock response
        mock_response = Mock()
        mock_response.content = b"<rss>...</rss>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Mock feedparser
        mock_feed = Mock()
        mock_feed.bozo = False
        mock_entry = Mock()
        mock_entry.title = "Test Article"
        mock_entry.summary = "Test summary"
        mock_entry.link = "https://example.com/test"
        mock_entry.published_parsed = timezone.now().timetuple()[:6]
        mock_entry.source = {"title": "Test Source"}
        mock_feed.entries = [mock_entry]
        mock_parse.return_value = mock_feed

        articles = service._fetch_rss_feed("test query")

        assert len(articles) == 1
        assert articles[0]["title"] == "Test Article"
        assert articles[0]["url"] == "https://example.com/test"
