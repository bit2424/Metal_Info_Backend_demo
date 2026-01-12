"""
Admin configuration for Metal News.
"""
from django.contrib import admin

from metal_news.models import Keyword, MetalNews, NewsKeyword


class NewsKeywordInline(admin.TabularInline):
    """Inline admin for NewsKeyword."""

    model = NewsKeyword
    extra = 1
    autocomplete_fields = ["keyword"]
    fields = ["keyword", "keyword_type"]


@admin.register(MetalNews)
class MetalNewsAdmin(admin.ModelAdmin):
    """Admin interface for MetalNews model."""

    list_display = ["title", "source", "published_at", "keyword_count", "created_at"]
    list_filter = ["source", "published_at", "created_at", "news_keywords__keyword_type"]
    search_fields = ["title", "description", "source"]
    readonly_fields = ["uuid", "created_at", "updated_at", "search_vector"]
    date_hierarchy = "published_at"
    ordering = ["-published_at"]
    inlines = [NewsKeywordInline]

    fieldsets = (
        ("Basic Information", {
            "fields": ("uuid", "title", "description", "url")
        }),
        ("Source & Publication", {
            "fields": ("source", "published_at")
        }),
        ("Search", {
            "fields": ("search_vector",),
            "classes": ("collapse",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def keyword_count(self, obj):
        """Display the number of keywords associated with this news."""
        return obj.news_keywords.count()
    keyword_count.short_description = "Keywords"


@admin.register(Keyword)
class KeywordAdmin(admin.ModelAdmin):
    """Admin interface for Keyword model."""

    list_display = ["name", "slug", "usage_count", "created_at"]
    search_fields = ["name", "slug"]
    readonly_fields = ["uuid", "slug", "created_at", "updated_at"]
    ordering = ["name"]

    fieldsets = (
        ("Keyword Information", {
            "fields": ("uuid", "name", "slug")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def usage_count(self, obj):
        """Display how many times this keyword is used."""
        return obj.news_keywords.count()
    usage_count.short_description = "Used in articles"


@admin.register(NewsKeyword)
class NewsKeywordAdmin(admin.ModelAdmin):
    """Admin interface for NewsKeyword model."""

    list_display = ["news_title", "keyword", "keyword_type", "created_at"]
    list_filter = ["keyword_type", "created_at"]
    search_fields = ["news__title", "keyword__name"]
    autocomplete_fields = ["news", "keyword"]
    readonly_fields = ["uuid", "created_at", "updated_at"]
    ordering = ["-created_at"]

    fieldsets = (
        ("Association", {
            "fields": ("uuid", "news", "keyword", "keyword_type")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def news_title(self, obj):
        """Display truncated news title."""
        return obj.news.title[:50] + "..." if len(obj.news.title) > 50 else obj.news.title
    news_title.short_description = "News Article"
