# Fetch Metal Prices Feature - Django REST Framework Requirements Document

## 1. Overview

This document outlines the requirements for implementing the **fetch-metal-prices** feature in Django REST Framework (DRF), based on the existing Supabase Edge Function implementation.

### 1.1 Current Implementation Summary (Supabase)

| Component | Technology |
|-----------|------------|
| Backend Function | Supabase Edge Function (Deno/TypeScript) |
| Database | PostgreSQL (via Supabase) |
| Client | Supabase JS Client |
| Frontend | React + Vite |

### 1.2 Target Implementation

| Component | Technology |
|-----------|------------|
| Backend API | Django REST Framework |
| Database | PostgreSQL |
| Task Queue | Celery (optional, for scheduled fetching) |
| Frontend | React (existing, with API client updates) |

---

## 2. External API Integration

### 2.1 API Endpoint

```
GET https://api.test.customer-app.metycle.com/api/v1/scrap-lizard/metal-prices/
```

### 2.2 Query Parameters

The API accepts multiple `metals` query parameters:

```
?metals=Aroma&metals=Berry&metals=Birch&metals=Candy&metals=Cliff&metals=Clove&metals=Elmo&metals=Taldon&metals=Tainttabor&metals=Tense&metals=Troma&metals=Zorba
```

### 2.3 Supported Metals

```python
SUPPORTED_METALS = [
    'Aroma',
    'Berry',
    'Birch',
    'Candy',
    'Cliff',
    'Clove',
    'Elmo',
    'Taldon',
    'Tainttabor',
    'Tense',
    'Troma',
    'Zorba',
]
```

### 2.4 External API Response Structure

```typescript
interface PricePoint {
  date: number;           // Unix timestamp (milliseconds)
  priceNormalised: number;  // Normalized price value
  priceType: string;        // Type of price (e.g., "spot", "future")
}

interface MetalPriceResponse {
  material: string;          // Metal name/identifier
  indicatorOne: number;      // First indicator value
  indicatorTwo: number;      // Second indicator value
  indicatorThree: number;    // Third indicator value
  chartIndicator: number;    // Chart indicator value
  lastDate: number;          // Last date timestamp (Unix ms)
  prices: PricePoint[];      // Array of historical prices
}
```

**Example Response:**
```json
[
  {
    "material": "Tense",
    "indicatorOne": 0.0234,
    "indicatorTwo": -0.0156,
    "indicatorThree": 0.0089,
    "chartIndicator": 0.0167,
    "lastDate": 1736294400000,
    "prices": [
      {
        "date": 1735689600000,
        "priceNormalised": 0.9823,
        "priceType": "spot"
      },
      {
        "date": 1735776000000,
        "priceNormalised": 0.9856,
        "priceType": "spot"
      }
    ]
  }
]
```

---

## 3. Database Schema

### 3.1 Django Model Definition

```python
# models.py
from django.db import models
import uuid


class MetalPrice(models.Model):
    """
    Stores metal price snapshots fetched from external API.
    Each record represents a single metal's price data at a specific fetch time.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    symbol = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Metal identifier/symbol"
    )
    name = models.CharField(
        max_length=100,
        help_text="Metal display name"
    )
    price_usd = models.DecimalField(
        max_digits=20,
        decimal_places=10,
        help_text="Latest normalized price value"
    )
    unit = models.CharField(
        max_length=50,
        default='normalized',
        help_text="Price unit type"
    )
    indicator_one = models.DecimalField(
        max_digits=20,
        decimal_places=10,
        null=True,
        blank=True,
        help_text="First indicator value"
    )
    indicator_two = models.DecimalField(
        max_digits=20,
        decimal_places=10,
        null=True,
        blank=True,
        help_text="Second indicator value"
    )
    indicator_three = models.DecimalField(
        max_digits=20,
        decimal_places=10,
        null=True,
        blank=True,
        help_text="Third indicator value"
    )
    chart_indicator = models.DecimalField(
        max_digits=20,
        decimal_places=10,
        null=True,
        blank=True,
        help_text="Chart indicator value"
    )
    last_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last date from external API"
    )
    price_history = models.JSONField(
        null=True,
        blank=True,
        help_text="Historical price data as JSON array"
    )
    fetched_at = models.DateTimeField(
        db_index=True,
        help_text="Timestamp when data was fetched from API"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Record creation timestamp"
    )

    class Meta:
        db_table = 'metal_prices'
        ordering = ['-fetched_at', 'symbol']
        indexes = [
            models.Index(fields=['symbol']),
            models.Index(fields=['-fetched_at']),
        ]

    def __str__(self):
        return f"{self.symbol} - {self.price_usd} ({self.fetched_at})"
```

### 3.2 Database Migration SQL (Reference)

```sql
-- PostgreSQL schema matching the current Supabase implementation
CREATE TABLE metal_prices (
    id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    price_usd NUMERIC(20, 10) NOT NULL,
    unit VARCHAR(50) NOT NULL DEFAULT 'normalized',
    indicator_one NUMERIC(20, 10),
    indicator_two NUMERIC(20, 10),
    indicator_three NUMERIC(20, 10),
    chart_indicator NUMERIC(20, 10),
    last_date TIMESTAMP WITH TIME ZONE,
    price_history JSONB,
    fetched_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_metal_prices_symbol ON metal_prices(symbol);
CREATE INDEX idx_metal_prices_fetched_at ON metal_prices(fetched_at DESC);
```

---

## 4. API Endpoints

### 4.1 Endpoint Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/metal-prices/` | Get latest metal prices |
| GET | `/api/v1/metal-prices/{symbol}/` | Get specific metal price |
| POST | `/api/v1/metal-prices/fetch/` | Trigger fetch from external API |
| GET | `/api/v1/metal-prices/history/` | Get price history by date range |

### 4.2 GET `/api/v1/metal-prices/`

**Description:** Retrieve the latest batch of metal prices.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `symbols` | string | No | Comma-separated list of metal symbols to filter |

**Response (200 OK):**
```json
{
  "success": true,
  "count": 12,
  "fetched_at": "2026-01-08T12:00:00Z",
  "data": [
    {
      "id": "uuid-here",
      "symbol": "Tense",
      "name": "Tense",
      "price_usd": "0.9856000000",
      "unit": "normalized",
      "indicator_one": "0.0234000000",
      "indicator_two": "-0.0156000000",
      "indicator_three": "0.0089000000",
      "chart_indicator": "0.0167000000",
      "last_date": "2026-01-08T00:00:00Z",
      "price_history": [
        {
          "date": 1735689600000,
          "priceNormalised": 0.9823,
          "priceType": "spot"
        }
      ],
      "fetched_at": "2026-01-08T12:00:00Z"
    }
  ]
}
```

### 4.3 POST `/api/v1/metal-prices/fetch/`

**Description:** Trigger a fresh fetch from the external API and store results.

**Request Body:** None required (optional filters)
```json
{
  "metals": ["Tense", "Troma"]  // Optional: specific metals to fetch
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Fetched and stored 12 metal prices",
  "inserted": 12,
  "fetched_at": "2026-01-08T12:00:00Z",
  "prices": [
    {
      "symbol": "Tense",
      "chart_indicator": "0.0167000000",
      "indicator_one": "0.0234000000",
      "price_history_count": 30
    }
  ]
}
```

**Response (500 Error):**
```json
{
  "success": false,
  "error": "Failed to fetch from external API: Connection timeout"
}
```

### 4.4 GET `/api/v1/metal-prices/{symbol}/`

**Description:** Get the latest price data for a specific metal.

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "uuid-here",
    "symbol": "Tense",
    "name": "Tense",
    "price_usd": "0.9856000000",
    "unit": "normalized",
    "indicator_one": "0.0234000000",
    "indicator_two": "-0.0156000000",
    "indicator_three": "0.0089000000",
    "chart_indicator": "0.0167000000",
    "last_date": "2026-01-08T00:00:00Z",
    "price_history": [...],
    "fetched_at": "2026-01-08T12:00:00Z"
  }
}
```

**Response (404 Not Found):**
```json
{
  "success": false,
  "error": "Metal with symbol 'InvalidMetal' not found"
}
```

---

## 5. Django REST Framework Implementation

### 5.1 Serializers

```python
# serializers.py
from rest_framework import serializers
from .models import MetalPrice


class PricePointSerializer(serializers.Serializer):
    """Serializer for price history points."""
    date = serializers.IntegerField()
    priceNormalised = serializers.FloatField()
    priceType = serializers.CharField()


class MetalPriceSerializer(serializers.ModelSerializer):
    """Serializer for MetalPrice model."""
    price_history = PricePointSerializer(many=True, read_only=True)

    class Meta:
        model = MetalPrice
        fields = [
            'id',
            'symbol',
            'name',
            'price_usd',
            'unit',
            'indicator_one',
            'indicator_two',
            'indicator_three',
            'chart_indicator',
            'last_date',
            'price_history',
            'fetched_at',
            'created_at',
        ]
        read_only_fields = fields


class MetalPriceSummarySerializer(serializers.Serializer):
    """Serializer for fetch response summary."""
    symbol = serializers.CharField()
    chart_indicator = serializers.DecimalField(max_digits=20, decimal_places=10)
    indicator_one = serializers.DecimalField(max_digits=20, decimal_places=10)
    price_history_count = serializers.IntegerField()


class FetchResponseSerializer(serializers.Serializer):
    """Serializer for the fetch endpoint response."""
    success = serializers.BooleanField()
    message = serializers.CharField()
    inserted = serializers.IntegerField()
    fetched_at = serializers.DateTimeField()
    prices = MetalPriceSummarySerializer(many=True)
```

### 5.2 Views

```python
# views.py
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

import requests
from django.db.models import Max
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import MetalPrice
from .serializers import MetalPriceSerializer, FetchResponseSerializer


SUPPORTED_METALS = [
    'Aroma', 'Berry', 'Birch', 'Candy', 'Cliff', 'Clove',
    'Elmo', 'Taldon', 'Tainttabor', 'Tense', 'Troma', 'Zorba',
]

EXTERNAL_API_URL = "https://api.test.customer-app.metycle.com/api/v1/scrap-lizard/metal-prices/"


class MetalPriceViewSet(ReadOnlyModelViewSet):
    """
    ViewSet for retrieving metal prices.
    """
    queryset = MetalPrice.objects.all()
    serializer_class = MetalPriceSerializer
    lookup_field = 'symbol'

    def get_queryset(self):
        """
        Return the latest batch of metal prices.
        """
        # Get the most recent fetched_at timestamp
        latest_fetch = MetalPrice.objects.aggregate(
            latest=Max('fetched_at')
        )['latest']

        if not latest_fetch:
            return MetalPrice.objects.none()

        queryset = MetalPrice.objects.filter(fetched_at=latest_fetch)

        # Optional filtering by symbols
        symbols = self.request.query_params.get('symbols')
        if symbols:
            symbol_list = [s.strip() for s in symbols.split(',')]
            queryset = queryset.filter(symbol__in=symbol_list)

        return queryset.order_by('symbol')

    def list(self, request: Request) -> Response:
        """List all latest metal prices."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        latest_fetch = queryset.first()
        fetched_at = latest_fetch.fetched_at if latest_fetch else None

        return Response({
            'success': True,
            'count': queryset.count(),
            'fetched_at': fetched_at,
            'data': serializer.data,
        })


class FetchMetalPricesView(APIView):
    """
    View to trigger fetching metal prices from external API.
    """

    def post(self, request: Request) -> Response:
        """
        Fetch metal prices from external API and store in database.
        """
        try:
            # Get optional metal filter from request
            metals = request.data.get('metals', SUPPORTED_METALS)

            # Build query parameters
            params = [('metals', metal) for metal in metals]

            # Fetch from external API
            response = requests.get(
                EXTERNAL_API_URL,
                params=params,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()

            if not isinstance(data, list):
                return Response(
                    {'success': False, 'error': 'Invalid API response format'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            fetched_at = timezone.now()
            prices_to_create = []
            summaries = []

            for metal_data in data:
                material = metal_data.get('material')
                if not material:
                    continue

                # Get latest price from prices array
                prices = metal_data.get('prices', [])
                latest_price = (
                    prices[-1]['priceNormalised']
                    if prices
                    else metal_data.get('chartIndicator', 0)
                )

                # Convert lastDate timestamp
                last_date_ts = metal_data.get('lastDate')
                last_date = (
                    datetime.fromtimestamp(last_date_ts / 1000, tz=timezone.utc)
                    if last_date_ts
                    else None
                )

                metal_price = MetalPrice(
                    symbol=material,
                    name=material,
                    price_usd=Decimal(str(latest_price)),
                    unit='normalized',
                    indicator_one=Decimal(str(metal_data.get('indicatorOne', 0))),
                    indicator_two=Decimal(str(metal_data.get('indicatorTwo', 0))),
                    indicator_three=Decimal(str(metal_data.get('indicatorThree', 0))),
                    chart_indicator=Decimal(str(metal_data.get('chartIndicator', 0))),
                    last_date=last_date,
                    price_history=prices,
                    fetched_at=fetched_at,
                )
                prices_to_create.append(metal_price)

                summaries.append({
                    'symbol': material,
                    'chart_indicator': metal_price.chart_indicator,
                    'indicator_one': metal_price.indicator_one,
                    'price_history_count': len(prices),
                })

            # Bulk create all prices
            MetalPrice.objects.bulk_create(prices_to_create)

            return Response({
                'success': True,
                'message': f'Fetched and stored {len(prices_to_create)} metal prices',
                'inserted': len(prices_to_create),
                'fetched_at': fetched_at,
                'prices': summaries,
            })

        except requests.RequestException as e:
            return Response(
                {'success': False, 'error': f'API request failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
```

### 5.3 URL Configuration

```python
# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MetalPriceViewSet, FetchMetalPricesView

router = DefaultRouter()
router.register(r'metal-prices', MetalPriceViewSet, basename='metal-prices')

urlpatterns = [
    path('api/v1/', include(router.urls)),
    path('api/v1/metal-prices/fetch/', FetchMetalPricesView.as_view(), name='fetch-metal-prices'),
]
```

---

## 6. Service Layer (Optional)

### 6.1 Metal Price Service

```python
# services.py
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional
import logging

import requests
from django.utils import timezone
from django.db import transaction

from .models import MetalPrice


logger = logging.getLogger(__name__)


class MetalPriceService:
    """
    Service class for metal price operations.
    """

    EXTERNAL_API_URL = "https://api.test.customer-app.metycle.com/api/v1/scrap-lizard/metal-prices/"
    
    SUPPORTED_METALS = [
        'Aroma', 'Berry', 'Birch', 'Candy', 'Cliff', 'Clove',
        'Elmo', 'Taldon', 'Tainttabor', 'Tense', 'Troma', 'Zorba',
    ]

    def fetch_and_store_prices(
        self,
        metals: Optional[List[str]] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Fetch metal prices from external API and store in database.

        Args:
            metals: Optional list of metal symbols to fetch
            timeout: Request timeout in seconds

        Returns:
            Dict with success status, message, and inserted count
        """
        metals = metals or self.SUPPORTED_METALS

        # Build query parameters
        params = [('metals', metal) for metal in metals]

        logger.info(f"Fetching prices for {len(metals)} metals from external API")

        try:
            response = requests.get(
                self.EXTERNAL_API_URL,
                params=params,
                timeout=timeout
            )
            response.raise_for_status()
            data = response.json()

        except requests.RequestException as e:
            logger.error(f"External API request failed: {e}")
            raise ExternalAPIError(f"Failed to fetch prices: {e}")

        if not isinstance(data, list):
            raise ExternalAPIError("Invalid API response format - expected array")

        return self._process_and_store(data)

    @transaction.atomic
    def _process_and_store(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process API response and store in database.
        """
        fetched_at = timezone.now()
        prices_to_create = []
        summaries = []

        for metal_data in data:
            material = metal_data.get('material')
            if not material:
                logger.warning(f"Skipping invalid metal data: {metal_data}")
                continue

            prices = metal_data.get('prices', [])
            latest_price = (
                prices[-1]['priceNormalised']
                if prices
                else metal_data.get('chartIndicator', 0)
            )

            last_date_ts = metal_data.get('lastDate')
            last_date = (
                datetime.fromtimestamp(last_date_ts / 1000, tz=timezone.utc)
                if last_date_ts
                else None
            )

            metal_price = MetalPrice(
                symbol=material,
                name=material,
                price_usd=Decimal(str(latest_price)),
                unit='normalized',
                indicator_one=Decimal(str(metal_data.get('indicatorOne', 0))),
                indicator_two=Decimal(str(metal_data.get('indicatorTwo', 0))),
                indicator_three=Decimal(str(metal_data.get('indicatorThree', 0))),
                chart_indicator=Decimal(str(metal_data.get('chartIndicator', 0))),
                last_date=last_date,
                price_history=prices,
                fetched_at=fetched_at,
            )
            prices_to_create.append(metal_price)

            summaries.append({
                'symbol': material,
                'chart_indicator': float(metal_price.chart_indicator),
                'indicator_one': float(metal_price.indicator_one),
                'price_history_count': len(prices),
            })

        MetalPrice.objects.bulk_create(prices_to_create)

        logger.info(f"Successfully stored {len(prices_to_create)} metal prices")

        return {
            'success': True,
            'message': f'Fetched and stored {len(prices_to_create)} metal prices',
            'inserted': len(prices_to_create),
            'fetched_at': fetched_at.isoformat(),
            'prices': summaries,
        }

    def get_latest_prices(
        self,
        symbols: Optional[List[str]] = None
    ) -> List[MetalPrice]:
        """
        Get the latest batch of metal prices.

        Args:
            symbols: Optional list of symbols to filter

        Returns:
            List of MetalPrice objects
        """
        from django.db.models import Max

        latest_fetch = MetalPrice.objects.aggregate(
            latest=Max('fetched_at')
        )['latest']

        if not latest_fetch:
            return []

        queryset = MetalPrice.objects.filter(fetched_at=latest_fetch)

        if symbols:
            queryset = queryset.filter(symbol__in=symbols)

        return list(queryset.order_by('symbol'))


class ExternalAPIError(Exception):
    """Exception raised for external API errors."""
    pass
```

---

## 7. Celery Task (Optional - Scheduled Fetching)

### 7.1 Celery Task Definition

```python
# tasks.py
from celery import shared_task
import logging

from .services import MetalPriceService, ExternalAPIError

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(ExternalAPIError,),
)
def fetch_metal_prices_task(self, metals=None):
    """
    Celery task to fetch metal prices from external API.

    Args:
        metals: Optional list of metal symbols to fetch

    Returns:
        Dict with fetch results
    """
    logger.info("Starting scheduled metal price fetch")

    try:
        service = MetalPriceService()
        result = service.fetch_and_store_prices(metals=metals)
        logger.info(f"Fetch completed: {result['message']}")
        return result

    except ExternalAPIError as e:
        logger.error(f"External API error: {e}")
        raise

    except Exception as e:
        logger.exception(f"Unexpected error in fetch task: {e}")
        raise
```

### 7.2 Celery Beat Schedule

```python
# celery.py (in Django settings)
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'fetch-metal-prices-hourly': {
        'task': 'metal_prices.tasks.fetch_metal_prices_task',
        'schedule': crontab(minute=0),  # Every hour
        'options': {'queue': 'metal_prices'},
    },
    'fetch-metal-prices-daily': {
        'task': 'metal_prices.tasks.fetch_metal_prices_task',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
        'options': {'queue': 'metal_prices'},
    },
}
```

---

## 8. Settings Configuration

### 8.1 Environment Variables

```bash
# .env
# External API
METAL_PRICES_API_URL=https://api.test.customer-app.metycle.com/api/v1/scrap-lizard/metal-prices/
METAL_PRICES_API_TIMEOUT=30

# Database
DATABASE_URL=postgres://user:password@localhost:5432/metal_market_watch

# Celery (optional)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 8.2 Django Settings

```python
# settings.py

METAL_PRICES_CONFIG = {
    'API_URL': env('METAL_PRICES_API_URL', default='https://api.test.customer-app.metycle.com/api/v1/scrap-lizard/metal-prices/'),
    'API_TIMEOUT': env.int('METAL_PRICES_API_TIMEOUT', default=30),
    'SUPPORTED_METALS': [
        'Aroma', 'Berry', 'Birch', 'Candy', 'Cliff', 'Clove',
        'Elmo', 'Taldon', 'Tainttabor', 'Tense', 'Troma', 'Zorba',
    ],
}

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # Add authentication as needed
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Metal prices are public
    ],
}
```

---

## 9. Frontend Integration Changes

### 9.1 API Client Updates

Replace Supabase client calls with fetch/axios calls to DRF endpoints:

```typescript
// api/metalPrices.ts

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface MetalPrice {
  id: string;
  symbol: string;
  name: string;
  price_usd: string;
  unit: string;
  indicator_one: string;
  indicator_two: string;
  indicator_three: string;
  chart_indicator: string;
  last_date: string | null;
  price_history: PricePoint[];
  fetched_at: string;
}

interface PricePoint {
  date: number;
  priceNormalised: number;
  priceType: string;
}

interface FetchResponse {
  success: boolean;
  message?: string;
  inserted?: number;
  fetched_at?: string;
  error?: string;
}

interface ListResponse {
  success: boolean;
  count: number;
  fetched_at: string;
  data: MetalPrice[];
}

export const metalPricesApi = {
  /**
   * Get latest metal prices from database
   */
  async getLatestPrices(symbols?: string[]): Promise<ListResponse> {
    const params = new URLSearchParams();
    if (symbols?.length) {
      params.set('symbols', symbols.join(','));
    }

    const response = await fetch(
      `${API_BASE_URL}/api/v1/metal-prices/?${params}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  },

  /**
   * Trigger fetch from external API
   */
  async fetchPrices(metals?: string[]): Promise<FetchResponse> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/metal-prices/fetch/`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: metals ? JSON.stringify({ metals }) : undefined,
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  },

  /**
   * Get specific metal price
   */
  async getMetalPrice(symbol: string): Promise<MetalPrice> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/metal-prices/${symbol}/`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data.data;
  },
};
```

### 9.2 Updated React Hook

```typescript
// hooks/useMetalPrices.ts
import { useState, useCallback, useEffect } from 'react';
import { metalPricesApi } from '@/api/metalPrices';
import { toast } from 'sonner';

export function useMetalPrices() {
  const [metalPrices, setMetalPrices] = useState<MetalPrice[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchPricesFromDb = useCallback(async () => {
    try {
      const response = await metalPricesApi.getLatestPrices();
      if (response.success && response.data) {
        setMetalPrices(response.data.map(transformMetalPrice));
      }
    } catch (error) {
      console.error('Error fetching prices:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const result = await metalPricesApi.fetchPrices();
      if (result.success) {
        await fetchPricesFromDb();
        toast.success('Prices updated', {
          description: `Fetched ${result.inserted || 0} metal prices from API.`,
        });
      }
    } catch (error) {
      console.error('Error:', error);
      toast.error('Failed to fetch prices', {
        description: error instanceof Error ? error.message : 'Unknown error',
      });
    } finally {
      setIsRefreshing(false);
    }
  }, [fetchPricesFromDb]);

  useEffect(() => {
    fetchPricesFromDb();
  }, [fetchPricesFromDb]);

  return {
    metalPrices,
    isLoading,
    isRefreshing,
    handleRefresh,
    refetch: fetchPricesFromDb,
  };
}

function transformMetalPrice(item: any): MetalPrice {
  return {
    id: item.symbol.toLowerCase(),
    name: item.name,
    symbol: item.symbol,
    price: parseFloat(item.price_usd),
    indicatorOne: parseFloat(item.indicator_one) || 0,
    indicatorTwo: parseFloat(item.indicator_two) || 0,
    indicatorThree: parseFloat(item.indicator_three) || 0,
    chartIndicator: parseFloat(item.chart_indicator) || 0,
    unit: item.unit,
    priceHistory: item.price_history || [],
    lastDate: item.last_date,
  };
}
```

---

## 10. Testing Requirements

### 10.1 Unit Tests

```python
# tests/test_services.py
import pytest
from unittest.mock import patch, Mock
from decimal import Decimal

from metal_prices.services import MetalPriceService, ExternalAPIError
from metal_prices.models import MetalPrice


@pytest.mark.django_db
class TestMetalPriceService:

    def test_fetch_and_store_prices_success(self, mock_api_response):
        """Test successful fetch and store operation."""
        with patch('requests.get') as mock_get:
            mock_get.return_value = Mock(
                status_code=200,
                json=lambda: mock_api_response
            )

            service = MetalPriceService()
            result = service.fetch_and_store_prices()

            assert result['success'] is True
            assert result['inserted'] == len(mock_api_response)
            assert MetalPrice.objects.count() == len(mock_api_response)

    def test_fetch_prices_api_error(self):
        """Test handling of API errors."""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("Connection failed")

            service = MetalPriceService()

            with pytest.raises(ExternalAPIError):
                service.fetch_and_store_prices()

    def test_get_latest_prices(self, sample_metal_prices):
        """Test retrieving latest prices."""
        service = MetalPriceService()
        prices = service.get_latest_prices()

        assert len(prices) > 0
        assert all(isinstance(p, MetalPrice) for p in prices)
```

### 10.2 API Tests

```python
# tests/test_views.py
import pytest
from rest_framework.test import APIClient
from rest_framework import status


@pytest.mark.django_db
class TestMetalPriceEndpoints:

    def setup_method(self):
        self.client = APIClient()

    def test_list_metal_prices(self, sample_metal_prices):
        """Test GET /api/v1/metal-prices/"""
        response = self.client.get('/api/v1/metal-prices/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'data' in response.data

    def test_fetch_metal_prices(self, mock_external_api):
        """Test POST /api/v1/metal-prices/fetch/"""
        response = self.client.post('/api/v1/metal-prices/fetch/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'inserted' in response.data

    def test_get_single_metal(self, sample_metal_prices):
        """Test GET /api/v1/metal-prices/{symbol}/"""
        response = self.client.get('/api/v1/metal-prices/Tense/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['symbol'] == 'Tense'
```

---

## 11. CORS Configuration

```python
# settings.py

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:3000",
    "https://your-production-domain.com",
]

CORS_ALLOW_METHODS = [
    "GET",
    "POST",
    "OPTIONS",
]

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "origin",
    "x-requested-with",
]
```

---

## 12. Project Structure

```
metal_prices/
├── __init__.py
├── admin.py
├── apps.py
├── models.py              # MetalPrice model
├── serializers.py         # DRF serializers
├── services.py            # Business logic
├── tasks.py               # Celery tasks
├── urls.py                # URL routing
├── views.py               # API views
├── tests/
│   ├── __init__.py
│   ├── conftest.py        # Pytest fixtures
│   ├── test_models.py
│   ├── test_services.py
│   └── test_views.py
└── migrations/
    └── 0001_initial.py
```

---

## 13. Comparison Summary

| Feature | Supabase Implementation | DRF Implementation |
|---------|------------------------|-------------------|
| Edge Function | `fetch-metal-prices/index.ts` | `FetchMetalPricesView` |
| Database Client | Supabase JS Client | Django ORM |
| Scheduled Jobs | Supabase Cron (external) | Celery Beat |
| Authentication | Supabase Auth / API Key | DRF Auth Classes |
| Row Level Security | PostgreSQL RLS | Django Permissions |
| Real-time | Supabase Realtime | WebSockets / Polling |
| Hosting | Supabase Edge | Any WSGI/ASGI server |

---

## 14. Migration Checklist

- [ ] Create Django project and app structure
- [ ] Define `MetalPrice` model and run migrations
- [ ] Implement serializers
- [ ] Implement views and URL routing
- [ ] Configure CORS for frontend
- [ ] Update frontend API client
- [ ] Set up Celery for scheduled tasks (optional)
- [ ] Write unit and integration tests
- [ ] Configure environment variables
- [ ] Deploy and test in staging environment

---

## 15. References

- Current Supabase Function: `supabase/functions/fetch-metal-prices/index.ts`
- Current Frontend: `src/pages/Index.tsx`
- Current Supabase Client: `src/integrations/supabase/client.ts`
- Current Database Types: `src/integrations/supabase/types.ts`
- Database Migrations: `supabase/migrations/`
