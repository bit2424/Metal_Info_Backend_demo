"""
Serializers for Metal News API.
"""
from rest_framework import serializers

from metal_news.models import Keyword, MetalNews, NewsKeyword


class KeywordSerializer(serializers.ModelSerializer):
    """Serializer for Keyword model."""

    class Meta:
        model = Keyword
        fields = ["uuid", "name", "slug"]
        read_only_fields = fields


class NewsKeywordSerializer(serializers.ModelSerializer):
    """Serializer for NewsKeyword with keyword details."""

    keyword = KeywordSerializer(read_only=True)

    class Meta:
        model = NewsKeyword
        fields = ["keyword", "keyword_type"]
        read_only_fields = fields


class MetalNewsSerializer(serializers.ModelSerializer):
    """Serializer for MetalNews model."""

    short_description = serializers.CharField(read_only=True)
    keywords_by_type = serializers.SerializerMethodField()

    class Meta:
        model = MetalNews
        fields = [
            "uuid",
            "title",
            "description",
            "short_description",
            "url",
            "source",
            "published_at",
            "created_at",
            "keywords_by_type",
        ]
        read_only_fields = fields

    def get_keywords_by_type(self, obj):
        """Group keywords by their type."""
        keywords_dict = {}
        news_keywords = obj.news_keywords.select_related("keyword").all()

        for nk in news_keywords:
            keyword_type = nk.keyword_type
            if keyword_type not in keywords_dict:
                keywords_dict[keyword_type] = []

            keywords_dict[keyword_type].append({
                "uuid": str(nk.keyword.uuid),
                "name": nk.keyword.name,
                "slug": nk.keyword.slug,
            })

        return keywords_dict


class MetalNewsListSerializer(serializers.ModelSerializer):
    """Serializer for listing MetalNews (without full description)."""

    short_description = serializers.CharField(read_only=True)
    keywords_by_type = serializers.SerializerMethodField()

    class Meta:
        model = MetalNews
        fields = [
            "uuid",
            "title",
            "short_description",
            "url",
            "source",
            "published_at",
            "keywords_by_type",
        ]
        read_only_fields = fields

    def get_keywords_by_type(self, obj):
        """Group keywords by their type."""
        keywords_dict = {}
        news_keywords = obj.news_keywords.select_related("keyword").all()

        for nk in news_keywords:
            keyword_type = nk.keyword_type
            if keyword_type not in keywords_dict:
                keywords_dict[keyword_type] = []

            keywords_dict[keyword_type].append({
                "uuid": str(nk.keyword.uuid),
                "name": nk.keyword.name,
                "slug": nk.keyword.slug,
            })

        return keywords_dict


class FetchNewsResponseSerializer(serializers.Serializer):
    """Serializer for the fetch news endpoint response."""

    success = serializers.BooleanField()
    message = serializers.CharField()
    inserted = serializers.IntegerField()
    skipped = serializers.IntegerField(required=False)
    total_fetched = serializers.IntegerField()


class ErrorResponseSerializer(serializers.Serializer):
    """Serializer for error responses."""

    success = serializers.BooleanField(default=False)
    error = serializers.CharField()


class SearchNewsSerializer(serializers.Serializer):
    """Serializer for search endpoint query params."""

    q = serializers.CharField(
        required=True,
        help_text="Search query",
        min_length=1
    )
