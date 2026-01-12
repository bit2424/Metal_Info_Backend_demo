# Metal Info Backend - API Documentation

## Quick Setup

```bash
# 1. Start all services
docker-compose up

# 2. Run migrations (first time only)
docker exec metal-info-backend python src/manage.py migrate

# 3. Verify API is running
curl http://localhost:8000/api/v1/metal-prices/
```

**Services Started:**
- PostgreSQL (port 5432)
- Django API (port 8000)
- Redis (port 6379)
- Celery Worker & Beat (background tasks)

---

## Base URL

```
http://localhost:8000/api/v1/
```

**Response Format:** All responses use camelCase and include a `success` field.

---

## Metal Prices API

### List Metal Prices

```http
GET /api/v1/metal-prices/
GET /api/v1/metal-prices/?symbols=Tense,Troma
```

**Response:**
```json
{
  "success": true,
  "count": 12,
  "fetchedAt": "2026-01-08T12:00:00Z",
  "data": [
    {
      "uuid": "...",
      "symbol": "Tense",
      "name": "Tense",
      "priceUsd": "0.9856000000",
      "unit": "normalized",
      "indicatorOne": "0.0234000000",
      "indicatorTwo": "-0.0156000000",
      "indicatorThree": "0.0089000000",
      "chartIndicator": "0.0167000000",
      "lastDate": "2026-01-08T00:00:00Z",
      "priceHistory": [
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
      ],
      "priceHistoryCount": 2,
      "fetchedAt": "2026-01-08T12:00:00Z",
      "createdAt": "2026-01-08T12:00:00Z"
    }
  ]
}
```

### Get Single Metal Price

```http
GET /api/v1/metal-prices/{symbol}/
```

### Fetch Fresh Prices

```http
POST /api/v1/metal-prices/fetch/
Content-Type: application/json

{"metals": ["Tense", "Troma"]}  # Optional - omit for all metals
```

**Supported Metals:** Aroma, Berry, Birch, Candy, Cliff, Clove, Elmo, Taldon, Tainttabor, Tense, Troma, Zorba

---

## Metal News API

### List News

```http
GET /api/v1/metal-news/
GET /api/v1/metal-news/?source=Reuters
GET /api/v1/metal-news/?keyword=copper
GET /api/v1/metal-news/?keyword=copper&keyword_type=related_metal
```

| Parameter | Description |
|-----------|-------------|
| source | Filter by news source |
| keyword | Filter by keyword name or slug |
| keyword_type | Filter by type: `topic`, `country`, `related_metal`, `industry`, `company`, `region` |

**Response:**
```json
{
  "success": true,
  "count": 50,
  "results": [
    {
      "uuid": "...",
      "title": "Copper Prices Surge in Asian Markets",
      "shortDescription": "Copper prices reached new highs...",
      "url": "https://example.com/news/copper",
      "source": "Metal Market News",
      "publishedAt": "2026-01-09T10:30:00Z",
      "keywordsByType": {
        "related_metal": [{"uuid": "...", "name": "Copper", "slug": "copper"}],
        "country": [{"uuid": "...", "name": "China", "slug": "china"}]
      }
    }
  ]
}
```

### Search News (Full-Text)

```http
GET /api/v1/metal-news/search/?q=copper+prices
```

Results are ranked by relevance (title > description > source).

### Get News Details

```http
GET /api/v1/metal-news/{uuid}/
```

### Fetch News Manually

```http
POST /api/v1/metal-news/fetch/
```

Triggers RSS feed fetch from Google News. Normally runs automatically every hour via Celery.

---

## Keywords API

### List Keywords

```http
GET /api/v1/keywords/
GET /api/v1/keywords/?type=related_metal
GET /api/v1/keywords/?search=copper
```

**Response:**
```json
{
  "success": true,
  "count": 3,
  "data": [
    {"uuid": "...", "name": "Copper", "slug": "copper"},
    {"uuid": "...", "name": "Steel", "slug": "steel"}
  ]
}
```

### Keyword Types

| Type | Description | Examples |
|------|-------------|----------|
| `related_metal` | Metals | Copper, Steel, Aluminum |
| `country` | Countries | China, USA, Brazil |
| `region` | Geographic regions | Asia, Europe |
| `industry` | Industry sectors | Mining, Manufacturing |
| `company` | Companies | BHP, Rio Tinto |
| `topic` | General themes | Prices, Supply Chain |

---

## Error Handling

```json
{
  "success": false,
  "error": "Error message here"
}
```

| Status | Description |
|--------|-------------|
| 200 | Success |
| 400 | Bad Request |
| 404 | Not Found |
| 500 | Server Error |

---

## Background Tasks (Celery)

News is fetched automatically every hour. To run manually:

```bash
# Via API
curl -X POST http://localhost:8000/api/v1/metal-news/fetch/

docker exec -it metal-info-backend python src/manage.py shell
>>> from metal_news.tasks import fetch_metal_news_task
>>> fetch_metal_news_task.delay()
```

**View Celery logs:**
```bash
docker logs metal-info-backend-celery-worker
```

---

## Admin Interface

Access: `http://localhost:8000/admin/`

- **Metal Prices:** View price history
- **Metal News:** Manage articles, add keywords inline
- **Keywords:** Create/manage reusable keywords

---

## Configuration

Key settings in `src/config/settings.py`:

```python
# News RSS search terms
METAL_NEWS_CONFIG = {
    "RSS_SEARCH_TERMS": ["copper prices", "steel industry news", ...],
    "FETCH_LIMIT": 50,
}

# Celery schedule (seconds)
CELERY_BEAT_SCHEDULE = {
    "fetch-metal-news-every-hour": {
        "task": "metal_news.tasks.fetch_metal_news_task",
        "schedule": 3600.0,
    },
}
```

---

## Quick Test Commands

```bash
# Metal Prices
curl http://localhost:8000/api/v1/metal-prices/
curl http://localhost:8000/api/v1/metal-prices/Tense/
curl -X POST http://localhost:8000/api/v1/metal-prices/fetch/

# Metal News
curl http://localhost:8000/api/v1/metal-news/
curl "http://localhost:8000/api/v1/metal-news/search/?q=copper"
curl "http://localhost:8000/api/v1/metal-news/?keyword=steel&keyword_type=related_metal"
curl -X POST http://localhost:8000/api/v1/metal-news/fetch/

# Keywords
curl http://localhost:8000/api/v1/keywords/
curl "http://localhost:8000/api/v1/keywords/?type=country"
```

---

## Running Tests

```bash
# All tests
docker exec metal-info-backend pytest src/

# Specific app
docker exec metal-info-backend pytest src/metal_news/tests/ -v
docker exec metal-info-backend pytest src/metal_prices/tests/ -v
```
