"""
Celery tasks for Metal News.
"""
import logging

from celery import shared_task

from metal_news.api.v1.services import NewsService, RSSFeedError

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def fetch_metal_news_task(self):
    """
    Periodic task to fetch metal industry news from RSS feeds.

    This task is scheduled to run hourly via Celery Beat.

    Returns:
        Dict with task execution results
    """
    logger.info("Starting fetch_metal_news_task")

    try:
        service = NewsService()
        result = service.fetch_and_store_news()

        logger.info(f"Task completed: {result['message']}")
        return result

    except RSSFeedError as e:
        logger.error(f"RSS feed error in task: {e}")
        # Retry the task after a delay (default: exponential backoff)
        raise self.retry(exc=e, countdown=60 * 5)  # Retry after 5 minutes

    except Exception as e:
        logger.exception(f"Unexpected error in fetch_metal_news_task: {e}")
        raise


@shared_task
def update_search_vectors_task():
    """
    Task to update search vectors for all news articles.

    This can be run manually or scheduled if needed to rebuild search indexes.
    """
    from django.contrib.postgres.search import SearchVector
    from metal_news.models import MetalNews

    logger.info("Starting update_search_vectors_task")

    try:
        # Update search vectors for all articles
        MetalNews.objects.update(
            search_vector=(
                SearchVector("title", weight="A") +
                SearchVector("description", weight="B") +
                SearchVector("source", weight="C")
            )
        )

        count = MetalNews.objects.count()
        logger.info(f"Updated search vectors for {count} articles")

        return {
            "success": True,
            "message": f"Updated search vectors for {count} articles",
            "updated": count,
        }

    except Exception as e:
        logger.exception(f"Error updating search vectors: {e}")
        raise
