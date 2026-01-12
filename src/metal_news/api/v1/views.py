"""
API views for Metal News.
"""
import logging

import attr
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from metal_news.models import Keyword, MetalNews
from shared.mixins import CamelSnakeCaseMixin

from .serializers import (
    ErrorResponseSerializer,
    FetchNewsResponseSerializer,
    KeywordSerializer,
    MetalNewsListSerializer,
    MetalNewsSerializer,
)
from .services import NewsService, RSSFeedError

logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class MetalNewsListView(CamelSnakeCaseMixin, generics.ListAPIView):
    """
    GET /api/v1/metal-news/
    List metal industry news articles.
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = MetalNewsListSerializer

    # Inject service
    news_service: NewsService = attr.ib(factory=NewsService)

    def get_queryset(self):
        """
        Return metal news articles ordered by publication date.
        
        Query parameters:
        - source: Filter by news source
        - keyword: Filter by keyword name or slug
        - keyword_type: Filter by keyword type (topic, country, related_metal, etc.)
        """
        queryset = MetalNews.objects.all().prefetch_related(
            "news_keywords__keyword"
        ).order_by("-published_at")

        # Filter by source
        source_param = self.request.query_params.get("source")
        if source_param:
            queryset = queryset.filter(source__icontains=source_param)

        # Filter by keyword (name or slug)
        keyword_param = self.request.query_params.get("keyword")
        if keyword_param:
            queryset = queryset.filter(
                news_keywords__keyword__name__iexact=keyword_param
            ) | queryset.filter(
                news_keywords__keyword__slug__iexact=keyword_param
            )

        # Filter by keyword type
        keyword_type_param = self.request.query_params.get("keyword_type")
        if keyword_type_param:
            queryset = queryset.filter(
                news_keywords__keyword_type__iexact=keyword_type_param
            )

        # Combine keyword and keyword_type filters if both present
        if keyword_param and keyword_type_param:
            queryset = MetalNews.objects.filter(
                news_keywords__keyword__name__iexact=keyword_param,
                news_keywords__keyword_type__iexact=keyword_type_param
            ) | MetalNews.objects.filter(
                news_keywords__keyword__slug__iexact=keyword_param,
                news_keywords__keyword_type__iexact=keyword_type_param
            )
            queryset = queryset.prefetch_related(
                "news_keywords__keyword"
            ).order_by("-published_at")

        # Remove duplicates that might occur from joins
        queryset = queryset.distinct()

        return queryset

    def list(self, request, *args, **kwargs):
        """List all metal news with custom response format."""
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "success": True,
            "count": queryset.count(),
            "data": serializer.data,
        })


@attr.s(auto_attribs=True)
class MetalNewsDetailView(CamelSnakeCaseMixin, generics.RetrieveAPIView):
    """
    GET /api/v1/metal-news/{uuid}/
    Retrieve a specific news article.
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = MetalNewsSerializer
    queryset = MetalNews.objects.all()
    lookup_field = "uuid"

    def retrieve(self, request, *args, **kwargs):
        """Retrieve news article with custom response format."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return Response({
            "success": True,
            "data": serializer.data,
        })


@attr.s(auto_attribs=True)
class MetalNewsSearchView(CamelSnakeCaseMixin, generics.ListAPIView):
    """
    GET /api/v1/metal-news/search/?q=copper
    Search metal news articles using full-text search.
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = MetalNewsListSerializer

    # Inject service
    news_service: NewsService = attr.ib(factory=NewsService)

    def get_queryset(self):
        """
        Return search results based on query parameter.
        """
        query = self.request.query_params.get("q", "").strip()

        if not query:
            return MetalNews.objects.none()

        return self.news_service.search_news(query)

    def list(self, request, *args, **kwargs):
        """List search results with custom response format."""
        query = request.query_params.get("q", "").strip()

        if not query:
            return Response({
                "success": False,
                "error": "Query parameter 'q' is required",
            }, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "success": True,
            "query": query,
            "count": queryset.count(),
            "data": serializer.data,
        })


@attr.s(auto_attribs=True)
class FetchMetalNewsView(CamelSnakeCaseMixin, APIView):
    """
    POST /api/v1/metal-news/fetch/
    Manually trigger fetching metal news from RSS feeds.
    """

    permission_classes = [permissions.AllowAny]

    # Inject service
    news_service: NewsService = attr.ib(factory=NewsService)

    def post(self, request):
        """
        Fetch metal news from RSS feeds and store in database.
        """
        try:
            result = self.news_service.fetch_and_store_news()

            # Serialize response
            response_serializer = FetchNewsResponseSerializer(data=result)
            response_serializer.is_valid(raise_exception=True)

            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK
            )

        except RSSFeedError as e:
            logger.error(f"RSS feed error: {e}")
            error_serializer = ErrorResponseSerializer(data={
                "success": False,
                "error": f"Failed to fetch from RSS feeds: {str(e)}"
            })
            error_serializer.is_valid(raise_exception=True)

            return Response(
                error_serializer.data,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        except Exception as e:
            logger.exception(f"Unexpected error in fetch view: {e}")
            error_serializer = ErrorResponseSerializer(data={
                "success": False,
                "error": str(e)
            })
            error_serializer.is_valid(raise_exception=True)

            return Response(
                error_serializer.data,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@attr.s(auto_attribs=True)
class KeywordListView(CamelSnakeCaseMixin, generics.ListAPIView):
    """
    GET /api/v1/keywords/
    List all available keywords.
    
    Query parameters:
    - type: Filter by keyword type (optional)
    - search: Search keywords by name (optional)
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = KeywordSerializer
    queryset = Keyword.objects.all()

    def get_queryset(self):
        """Return keywords with optional filtering."""
        queryset = Keyword.objects.all().order_by("name")

        # Filter by type (shows keywords that have been used with this type)
        keyword_type_param = self.request.query_params.get("type")
        if keyword_type_param:
            queryset = queryset.filter(
                news_keywords__keyword_type__iexact=keyword_type_param
            ).distinct()

        # Search by name
        search_param = self.request.query_params.get("search")
        if search_param:
            queryset = queryset.filter(name__icontains=search_param)

        return queryset

    def list(self, request, *args, **kwargs):
        """List all keywords with custom response format."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        return Response({
            "success": True,
            "count": queryset.count(),
            "data": serializer.data,
        })
