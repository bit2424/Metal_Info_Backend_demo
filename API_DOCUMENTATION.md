# API Documentation

Complete API reference for the Metal Info Backend.

## Base URL

```
http://localhost:8000/api/v1/
```

---

## Endpoints

### 1. List Latest Metal Prices

Retrieve the most recent batch of metal prices from the database.

**Endpoint:** `GET /api/v1/metal-prices/`

**Query Parameters:**

| Parameter | Type   | Required | Description                                |
|-----------|--------|----------|--------------------------------------------|
| symbols   | string | No       | Comma-separated list of metal symbols      |

**Example Requests:**

```bash
# Get all latest prices
curl http://localhost:8000/api/v1/metal-prices/

# Filter by specific metals
curl "http://localhost:8000/api/v1/metal-prices/?symbols=Tense,Troma,Zorba"
```

**Success Response (200 OK):**

```json
{
  "success": true,
  "count": 3,
  "fetchedAt": "2026-01-08T12:00:00Z",
  "data": [
    {
      "uuid": "123e4567-e89b-12d3-a456-426614174000",
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

---

### 2. Get Metal Price by Symbol

Retrieve the latest price for a specific metal.

**Endpoint:** `GET /api/v1/metal-prices/{symbol}/`

**Path Parameters:**

| Parameter | Type   | Required | Description        |
|-----------|--------|----------|--------------------|
| symbol    | string | Yes      | Metal symbol name  |

**Example Request:**

```bash
curl http://localhost:8000/api/v1/metal-prices/Tense/
```

**Success Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "uuid": "123e4567-e89b-12d3-a456-426614174000",
    "symbol": "Tense",
    "name": "Tense",
    "priceUsd": "0.9856000000",
    "unit": "normalized",
    "indicatorOne": "0.0234000000",
    "indicatorTwo": "-0.0156000000",
    "indicatorThree": "0.0089000000",
    "chartIndicator": "0.0167000000",
    "lastDate": "2026-01-08T00:00:00Z",
    "priceHistory": [...],
    "priceHistoryCount": 30,
    "fetchedAt": "2026-01-08T12:00:00Z",
    "createdAt": "2026-01-08T12:00:00Z"
  }
}
```

**Error Response (404 Not Found):**

```json
{
  "detail": "Metal with symbol 'InvalidMetal' not found"
}
```

---

### 3. Fetch Metal Prices from External API

Trigger a fresh fetch from the external API and store the results in the database.

**Endpoint:** `POST /api/v1/metal-prices/fetch/`

**Request Body (Optional):**

```json
{
  "metals": ["Tense", "Troma", "Zorba"]
}
```

If no body is provided, all supported metals will be fetched.

**Example Requests:**

```bash
# Fetch all metals
curl -X POST http://localhost:8000/api/v1/metal-prices/fetch/ \
  -H "Content-Type: application/json"

# Fetch specific metals
curl -X POST http://localhost:8000/api/v1/metal-prices/fetch/ \
  -H "Content-Type: application/json" \
  -d '{"metals": ["Tense", "Troma"]}'
```

**Success Response (200 OK):**

```json
{
  "success": true,
  "message": "Fetched and stored 12 metal prices",
  "inserted": 12,
  "fetchedAt": "2026-01-08T12:00:00Z",
  "prices": [
    {
      "symbol": "Tense",
      "chartIndicator": "0.0167000000",
      "indicatorOne": "0.0234000000",
      "priceHistoryCount": 30
    },
    {
      "symbol": "Troma",
      "chartIndicator": "0.0098000000",
      "indicatorOne": "0.0145000000",
      "priceHistoryCount": 28
    }
  ]
}
```

**Error Response (500 Internal Server Error):**

```json
{
  "success": false,
  "error": "Failed to fetch from external API: Connection timeout"
}
```

---

## Supported Metals

The following metal symbols are supported by the API:

- `Aroma`
- `Berry`
- `Birch`
- `Candy`
- `Cliff`
- `Clove`
- `Elmo`
- `Taldon`
- `Tainttabor`
- `Tense`
- `Troma`
- `Zorba`

---

## Response Field Descriptions

### MetalPrice Object

| Field              | Type     | Description                                    |
|--------------------|----------|------------------------------------------------|
| uuid               | string   | Unique identifier (UUID)                       |
| symbol             | string   | Metal identifier/symbol                        |
| name               | string   | Metal display name                             |
| priceUsd           | string   | Latest normalized price value (decimal)        |
| unit               | string   | Price unit type (usually "normalized")         |
| indicatorOne       | string   | First indicator value (decimal)                |
| indicatorTwo       | string   | Second indicator value (decimal)               |
| indicatorThree     | string   | Third indicator value (decimal)                |
| chartIndicator     | string   | Chart indicator value (decimal)                |
| lastDate           | string   | Last date from external API (ISO 8601)         |
| priceHistory       | array    | Array of historical price points               |
| priceHistoryCount  | integer  | Count of price history entries                 |
| fetchedAt          | string   | When data was fetched from API (ISO 8601)      |
| createdAt          | string   | Record creation timestamp (ISO 8601)           |

### PricePoint Object

| Field           | Type    | Description                              |
|-----------------|---------|------------------------------------------|
| date            | integer | Unix timestamp in milliseconds           |
| priceNormalised | float   | Normalized price value                   |
| priceType       | string  | Type of price (e.g., "spot", "future")   |

---

## Case Conversion

The API automatically converts between camelCase and snake_case:

- **Request data**: Accepts both camelCase and snake_case
- **Response data**: Always returns camelCase

**Examples:**

```javascript
// Frontend sends (camelCase)
{
  "metals": ["Tense"]
}

// Backend receives (snake_case)
{
  "metals": ["Tense"]
}

// Backend sends (snake_case internally)
{
  "price_usd": "0.9856",
  "chart_indicator": "0.0167"
}

// Frontend receives (camelCase)
{
  "priceUsd": "0.9856",
  "chartIndicator": "0.0167"
}
```

---

## Error Handling

### Standard Error Response

```json
{
  "success": false,
  "error": "Error message here"
}
```

### HTTP Status Codes

| Status Code | Description                                      |
|-------------|--------------------------------------------------|
| 200         | Success                                          |
| 400         | Bad Request (invalid input)                      |
| 404         | Not Found (resource doesn't exist)               |
| 500         | Internal Server Error (server/API error)         |

---

## Rate Limiting

Currently, there are no rate limits implemented. In a production environment, consider adding:

- Rate limiting middleware
- API throttling
- Request authentication

---

## Testing the API

### Using curl

```bash
# List prices
curl http://localhost:8000/api/v1/metal-prices/

# Get specific metal
curl http://localhost:8000/api/v1/metal-prices/Tense/

# Fetch new prices
curl -X POST http://localhost:8000/api/v1/metal-prices/fetch/ \
  -H "Content-Type: application/json"
```

### Using Postman

1. Import the collection (create one from the examples above)
2. Set base URL: `http://localhost:8000`
3. Test each endpoint

### Using Python

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# List prices
response = requests.get(f"{BASE_URL}/metal-prices/")
print(response.json())

# Fetch new prices
response = requests.post(
    f"{BASE_URL}/metal-prices/fetch/",
    json={"metals": ["Tense", "Troma"]}
)
print(response.json())
```

### Using JavaScript/TypeScript

```typescript
const BASE_URL = "http://localhost:8000/api/v1";

// List prices
const response = await fetch(`${BASE_URL}/metal-prices/`);
const data = await response.json();
console.log(data);

// Fetch new prices
const fetchResponse = await fetch(`${BASE_URL}/metal-prices/fetch/`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify({ metals: ["Tense", "Troma"] })
});
const fetchData = await fetchResponse.json();
console.log(fetchData);
```

---

## CORS Configuration

The API is configured to accept requests from:

- `http://localhost:5173` (Vite dev server)
- `http://localhost:3000` (React dev server)

To add more origins, update the `CORS_ALLOWED_ORIGINS` in your `.env` file.

---

## Next Steps

- Implement authentication for production use
- Add rate limiting
- Set up monitoring and logging
- Deploy to production environment
- Add more endpoints as needed
