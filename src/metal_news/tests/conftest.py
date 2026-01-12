"""
Pytest configuration and fixtures for metal_news tests.
"""
import pytest
from django.utils import timezone


@pytest.fixture
def sample_rss_entry():
    """Sample RSS feed entry for testing."""
    return {
        "title": "Copper Prices Surge to Record Highs",
        "summary": "Copper prices reached new record highs today amid strong demand from electric vehicle manufacturers.",
        "link": "https://example.com/news/copper-prices-surge",
        "source": {"title": "Metal Industry News"},
        "published_parsed": timezone.now().timetuple()[:6],
    }


@pytest.fixture
def sample_article_data():
    """Sample article data for testing."""
    return {
        "title": "Steel Industry Faces Supply Chain Challenges",
        "description": "The global steel industry is grappling with supply chain disruptions.",
        "url": "https://example.com/news/steel-supply-chain",
        "source": "Industry Weekly",
        "published_at": timezone.now(),
    }
