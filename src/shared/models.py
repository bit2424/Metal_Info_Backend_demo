"""
Shared base models for the project.
"""
import uuid

from django.db import models


class UUIDTimeStampedAbstractModel(models.Model):
    """
    Abstract base model providing UUID primary key and timestamp fields.
    """
    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="UUID primary key"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Record creation timestamp"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Record last update timestamp"
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]
