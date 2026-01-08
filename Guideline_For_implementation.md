# 🛠️ Metycle Backend Prompt Guide

A concise guide for AI prompts when creating new features or projects following Metycle's patterns and standards.

---

## 📦 Tech Stack

```yaml
Python: 3.13.x
Framework: Django 5.x + Django REST Framework 3.x
Database: PostgreSQL
Task Queue: Celery + SQS
Package Manager: Poetry
Linting: Ruff
Testing: Pytest + Factory Boy
Deployment: AWS Copilot
```

---

## 🏗️ Project Structure

```
src/
├── shared/              # Reusable utilities (email, slack, whatsapp, etc.)
├── accounts/            # User, Company, Profile models
├── integrations/        # Third-party integrations (pipedrive)
├── [domain]/            # Business domain apps (orders, trading, etc.)
│   ├── api/
│   │   └── v1/
│   │       ├── urls.py
│   │       ├── views.py
│   │       ├── serializers.py
│   │       └── services.py  # Business logic
│   ├── models/
│   │   └── __init__.py      # Export models
│   ├── choices.py           # TextChoices enums
│   ├── signals.py           # Django signals
│   ├── tasks.py             # Celery tasks
│   ├── receivers.py         # Signal receivers
│   └── tests/
│       ├── conftest.py      # Fixtures
│       ├── factories.py     # Factory Boy factories
│       └── api/v1/
│           └── test_views.py
```

### Dependency Rules
- `shared` → imported by all apps (generalized, abstracted code)
- `integrations` → imports from core apps, NOT the other way around
- Use Django signals to decouple `integrations` from core apps

---

## 📝 Code Standards

### Models

```python
from django.db import models
from safedelete import SOFT_DELETE
from safedelete.models import SafeDeleteModel
from shared.django_commons.models import UUIDTimeStampedAbstractModel


class MyModel(UUIDTimeStampedAbstractModel, SafeDeleteModel):
    """Docstring describing the model."""
    
    _safedelete_policy = SOFT_DELETE
    
    # Fields with inline docstrings
    """ field description """
    name = models.CharField(max_length=257)
    """ related object """
    company = models.ForeignKey(
        db_index=True,
        to="accounts.Company",
        related_name="items",
        on_delete=models.PROTECT,
        verbose_name="Company",
    )
    
    class Meta:
        db_table = "my_model"
        verbose_name = "My Model"
        verbose_name_plural = "My Models"
    
    @property
    def computed_field(self) -> str:
        return f"{self.name} computed"
```

### Choices (Enums)

```python
from django.db import models


class MyStatus(models.TextChoices):
    PENDING = "status.pending", "Pending"
    ACTIVE = "status.active", "Active"
    COMPLETED = "status.completed", "Completed"
```

### Views

```python
import attr
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from shared.django_commons.authentication import CsrfExemptSessionAuthentication
from shared.django_commons.drf.mixins import CamelSnakeCaseMixin
from shared.django_commons.drf.permissions import IsAnonymous


@attr.s(auto_attribs=True)
class MyCreateView(CamelSnakeCaseMixin, generics.CreateAPIView):
    """View docstring."""
    
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = (CsrfExemptSessionAuthentication,)
    serializer_class = MySerializer
    
    # Inject services using attr.ib
    my_service: MyService = attr.ib(factory=MyService)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Business logic via service
        result = self.my_service.do_something(serializer.validated_data)
        return Response(status=status.HTTP_201_CREATED)
```

### Serializers

```python
from rest_framework import serializers, exceptions


class MySerializer(serializers.ModelSerializer):
    """Always use ModelSerializer when possible."""
    
    # Nested source mapping
    company_name = serializers.CharField(source="company.name")
    
    class Meta:
        model = MyModel
        fields = ["uuid", "name", "company_name", "created_at"]
    
    def validate_name(self, name):
        """Field-level validation."""
        if len(name) < 3:
            raise serializers.ValidationError("Name too short")
        return name
    
    def create(self, validated_data):
        # Custom create logic
        return super().create(validated_data)
```

### Services (Business Logic)

```python
import logging
from django.db import transaction

logger = logging.getLogger(__name__)


class MyService:
    """Encapsulate business logic in services."""
    
    def create_item(self, user_id: int, data: dict) -> MyModel:
        with transaction.atomic():
            item = MyModel.objects.create(**data)
            # Side effects
            my_signal.send(sender=self.__class__, item=item)
            logger.info(f"Created item {item.uuid}")
            return item
```

### URLs

```python
from django.urls import path
from .views import MyView, MyDetailView

app_name = "my_app"

urlpatterns = [
    path("items/", MyView.as_view(), name="item-list"),
    path("items/<str:item_uuid>/", MyDetailView.as_view(), name="item-detail"),
]
```

---

## 🧪 Testing Standards

### Factories (Factory Boy)

```python
import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyDecimal, FuzzyText

from my_app.models import MyModel
from shared.choices import MetalTypes


class MyModelFactory(DjangoModelFactory):
    class Meta:
        model = MyModel
    
    name = FuzzyText(prefix="Item-")
    metal_type = FuzzyChoice(MetalTypes.values)
    quantity = FuzzyDecimal(low=15.00000, high=9999999.99999)
    company = factory.SubFactory(CompanyFactory)
    creator = factory.SubFactory(UserFactory)
```

### Test Fixtures (conftest.py)

```python
import pytest
from rest_framework.test import APIClient
from my_app.tests.factories import MyModelFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_login(user)
    return api_client


@pytest.fixture
def valid_payload() -> dict:
    return {
        "name": "Test Item",
        "metalType": "metal.type.aluminium",
        "quantity": 100.00000,
    }
```

### Test Views

```python
import pytest
from unittest import mock
from django.urls import reverse
from rest_framework import status
from factory.django import mute_signals

from my_app.signals import item_created


@pytest.mark.django_db
@mute_signals(item_created)  # Mute signals to isolate tests
@mock.patch("shared.email.tasks.send_async_email.delay", return_value=None)
def test_create_item_success(
    mocked_send_email,
    authenticated_client,
    valid_payload,
):
    endpoint = reverse("api:v1:my_app:item-list")
    response = authenticated_client.post(
        path=endpoint,
        data=valid_payload,
        format="json"
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    assert mocked_send_email.call_count == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        pytest.param("name", "", "This field may not be blank.", id="empty_name"),
        pytest.param("quantity", -1, "Ensure this value is greater than 0.", id="negative_qty"),
    ],
)
def test_create_item_validation_errors(authenticated_client, valid_payload, field, value, error):
    valid_payload[field] = value
    endpoint = reverse("api:v1:my_app:item-list")
    response = authenticated_client.post(path=endpoint, data=valid_payload, format="json")
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert error in str(response.json())
```

---

## 🔧 Configuration

### pyproject.toml Key Settings

```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "metycle.settings.pytest"
addopts = "--reuse-db -v"
pythonpath = [".", "src"]
python_files = "test_*.py"
testpaths = ["src"]

[tool.ruff]
line-length = 120
target-version = "py313"
exclude = ["migrations", ".venv"]

[tool.ruff.lint]
select = ["E", "F", "B", "I", "UP", "C4", "SIM", "T20", "Q", "RUF"]
```

### Pre-commit Hooks

```yaml
# Runs automatically on commit
- trailing-whitespace
- end-of-file-fixer
- check-yaml
- check-added-large-files
- ruff (lint + fix)
- ruff (format)
```

---

## 🚀 Celery Tasks

```python
from celery import shared_task
from metycle.celery import app


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=60,  # seconds
    retry_kwargs={"max_retries": 4},
)
def process_item(self, item_id: int):
    """Task with exponential backoff retry."""
    from my_app.models import MyModel
    
    item = MyModel.objects.get(id=item_id)
    # Process logic
    return {"status": "success", "item_id": item_id}
```

---

## 📡 Signals Pattern

```python
# signals.py
from django.dispatch import Signal

item_created = Signal()
item_updated = Signal()

# receivers.py
from django.dispatch import receiver
from my_app.signals import item_created


@receiver(item_created)
def handle_item_created(sender, item, **kwargs):
    """React to item creation - send to integrations, etc."""
    # Use signals to decouple integrations from core logic
    pass
```

---

## 🔐 Authentication Patterns

```python
# For public endpoints (signup, login)
permission_classes = [IsAnonymous]
authentication_classes = (SessionAuthentication,)

# For authenticated endpoints
permission_classes = [permissions.IsAuthenticated]
authentication_classes = (CsrfExemptSessionAuthentication,)

# For internal/API token endpoints
permission_classes = [permissions.IsAuthenticated]
authentication_classes = (TokenAuthentication,)
```

---

## 📋 Makefile Commands

```bash
make run-server         # Start development server
make test               # Run all tests
make test <keyword>     # Run tests matching keyword
make lint               # Run linting
make migrate            # Run migrations
make makemigrations     # Create migrations
make shell              # Django shell
make update             # Install deps + migrate + pre-commit
```

---

## ✅ Checklist for New Features

1. **Models**
   - [ ] Inherit from `UUIDTimeStampedAbstractModel` + `SafeDeleteModel`
   - [ ] Use `SOFT_DELETE` policy
   - [ ] Add `db_table` in Meta
   - [ ] Add `db_index=True` on ForeignKeys

2. **API**
   - [ ] Use `CamelSnakeCaseMixin` for auto case conversion
   - [ ] Inject services with `@attr.s(auto_attribs=True)`
   - [ ] Use `transaction.atomic()` for multi-operation writes

3. **Testing**
   - [ ] Create factories in `tests/factories.py`
   - [ ] Create fixtures in `tests/conftest.py`
   - [ ] Use `@pytest.mark.django_db`
   - [ ] Mock external services and signals
   - [ ] Use parametrize for validation tests

4. **Signals**
   - [ ] Define signals for cross-app communication
   - [ ] Use receivers in integrations app
   - [ ] Mute signals in tests with `@mute_signals`

5. **Documentation**
   - [ ] Add docstrings to classes and complex methods
   - [ ] Update README if adding new setup steps

---

## 🎯 Prompt Template

When prompting for new features, include:

```markdown
## Context
- App location: src/[app_name]/
- Related models: [existing models if extending]
- Integration points: [signals, services to use]

## Requirements
- [Specific feature requirements]
- [API endpoints needed]
- [Business rules]

## Standards
- Follow Metycle patterns (CamelSnakeCaseMixin, attr.s services)
- Soft delete with SafeDeleteModel
- UUID primary keys
- Pytest with Factory Boy
- Mocked external services in tests
```

---