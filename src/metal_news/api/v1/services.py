"""
Business logic services for Metal News.
"""
import logging
from datetime import datetime, timezone as dt_timezone
from typing import Any
from urllib.parse import urlencode

import feedparser
import requests
from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db import transaction
from django.db.utils import IntegrityError
from django.db.models import QuerySet
from django.utils import timezone

from metal_news.models import MetalNews

logger = logging.getLogger(__name__)


class RSSFeedError(Exception):
    """Exception raised for RSS feed errors."""
    pass


class NewsService:
    """
    Service class for metal news operations.
    """

    def __init__(self):
        self.config = settings.METAL_NEWS_CONFIG
        self.rss_base_url = self.config["RSS_BASE_URL"]
        self.rss_params = self.config["RSS_PARAMS"]
        self.search_terms = self.config["RSS_SEARCH_TERMS"]
        self.fetch_limit = self.config["FETCH_LIMIT"]
        self.request_timeout = self.config["REQUEST_TIMEOUT"]

    def fetch_and_store_news(self) -> dict[str, Any]:
        """
        Fetch metal news from Google News RSS feeds and store in database.

        Returns:
            Dict with success status, message, and inserted count

        Raises:
            RSSFeedError: If the RSS feed request fails
        """
        logger.info(f"Fetching news for {len(self.search_terms)} search terms")

        all_articles = []
        for search_term in self.search_terms:
            try:
                articles = self._fetch_rss_feed(search_term)
                all_articles.extend(articles)
            except Exception as e:
                logger.error(f"Error fetching RSS feed for '{search_term}': {e}")
                continue

        if not all_articles:
            logger.warning("No articles fetched from any RSS feed")
            return {
                "success": True,
                "message": "No new articles found",
                "inserted": 0,
                "total_fetched": 0,
            }

        # Remove duplicates based on URL
        unique_articles = {article["url"]: article for article in all_articles}
        logger.info(f"Fetched {len(unique_articles)} unique articles")

        return self._process_and_store(list(unique_articles.values()))

    def _fetch_rss_feed(self, search_term: str) -> list[dict[str, Any]]:
        """
        Fetch articles from Google News RSS feed for a specific search term.

        Args:
            search_term: The search query for Google News

        Returns:
            List of article dictionaries

        Raises:
            RSSFeedError: If the RSS feed request fails
        """
        # Build RSS feed URL
        params = {
            "q": search_term,
            **self.rss_params
        }
        rss_url = f"{self.rss_base_url}?{urlencode(params)}"

        logger.debug(f"Fetching RSS feed: {rss_url}")

        try:
            # Fetch RSS feed with requests (feedparser can parse from URL, but we want timeout control)
            response = requests.get(rss_url, timeout=self.request_timeout)
            response.raise_for_status()

            # Parse RSS feed
            feed = feedparser.parse(response.content)

            if feed.bozo:
                logger.warning(f"RSS feed parsing warning: {feed.bozo_exception}")

            articles = []
            for entry in feed.entries[:self.fetch_limit]:
                try:
                    # Parse publication date
                    published_at = None
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        published_at = datetime(*entry.published_parsed[:6], tzinfo=dt_timezone.utc)
                    elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                        published_at = datetime(*entry.updated_parsed[:6], tzinfo=dt_timezone.utc)
                    else:
                        published_at = timezone.now()

                    article = {
                        "title": entry.get("title", "No title"),
                        "description": entry.get("summary", ""),
                        "url": entry.get("link", ""),
                        "source": entry.get("source", {}).get("title", "Google News"),
                        "published_at": published_at,
                    }

                    # Skip articles without URL
                    if not article["url"]:
                        continue

                    articles.append(article)

                except Exception as e:
                    logger.warning(f"Error parsing RSS entry: {e}")
                    continue

            logger.info(f"Fetched {len(articles)} articles for '{search_term}'")
            return articles

        except requests.RequestException as e:
            logger.error(f"RSS feed request failed: {e}")
            raise RSSFeedError(f"Failed to fetch RSS feed: {e}") from e

    def _process_and_store(self, articles: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Process fetched articles and store in database.

        Args:
            articles: List of article data dictionaries

        Returns:
            Dict with processing results
        """
        inserted_count = 0
        skipped_count = 0

        for article_data in articles:
            try:
                with transaction.atomic():
                    url = article_data["url"]

                    # Check if article already exists (by URL)
                    if MetalNews.objects.filter(url=url).exists():
                        skipped_count += 1
                        continue

                    MetalNews.objects.create(
                        title=article_data["title"],
                        description=article_data["description"],
                        url=url,
                        source=article_data["source"],
                        published_at=article_data["published_at"],
                    )
                    inserted_count += 1

            except IntegrityError as e:
                # If we raced another insert (or hit unique constraints), treat as skipped.
                logger.warning(
                    "Skipping article due to DB integrity error: %s (%s)",
                    article_data.get("title"),
                    e,
                )
                skipped_count += 1
                continue
            except Exception:
                # Log full stack so we can see the root cause (e.g., URL too long, bad encoding, etc.)
                logger.exception("Error storing article '%s'", article_data.get("title"))
                continue

        logger.info(f"Stored {inserted_count} new articles, skipped {skipped_count} duplicates")

        return {
            "success": True,
            "message": f"Fetched and stored {inserted_count} new articles",
            "inserted": inserted_count,
            "skipped": skipped_count,
            "total_fetched": len(articles),
        }

    def search_news(self, query: str) -> QuerySet[MetalNews]:
        """
        Search news articles using PostgreSQL full-text search.

        Args:
            query: Search query string

        Returns:
            QuerySet of MetalNews objects ordered by relevance
        """
        if not query or not query.strip():
            return MetalNews.objects.none()

        # Create search query
        search_query = SearchQuery(query)

        # Filter and rank by search vector
        queryset = MetalNews.objects.annotate(
            rank=SearchRank("search_vector", search_query)
        ).filter(search_vector=search_query).order_by("-rank", "-published_at")

        return queryset

    def get_latest_news(self, limit: int = 20) -> list[MetalNews]:
        """
        Get the latest metal news articles.

        Args:
            limit: Maximum number of articles to return

        Returns:
            List of MetalNews objects
        """
        return list(MetalNews.objects.order_by("-published_at")[:limit])

    def get_news_by_source(self, source: str) -> QuerySet[MetalNews]:
        """
        Get news articles from a specific source.

        Args:
            source: News source name

        Returns:
            QuerySet of MetalNews objects
        """
        return MetalNews.objects.filter(source=source).order_by("-published_at")
