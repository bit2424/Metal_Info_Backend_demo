# Metal Info Backend - Django REST Framework

A Django REST Framework application for fetching and storing metal prices from an external API.

## 🚀 Features

- **Fetch Metal Prices**: Fetch real-time metal prices from external API
- **Store Historical Data**: Store price snapshots with timestamps
- **RESTful API**: Clean API endpoints for accessing metal price data
- **Docker Support**: Easy setup with Docker Compose
- **Comprehensive Testing**: Full test coverage with pytest and Factory Boy
- **Auto Case Conversion**: Automatic camelCase ↔ snake_case conversion for API requests/responses

## 📋 Requirements

- Python 3.13+
- PostgreSQL 16+
- Poetry (for dependency management)
- Docker & Docker Compose (for containerized setup)

## 🛠️ Tech Stack

- **Framework**: Django 5.x + Django REST Framework 3.x
- **Database**: PostgreSQL
- **Package Manager**: Poetry
- **Testing**: Pytest + Factory Boy
- **Linting**: Ruff
- **Containerization**: Docker + Docker Compose

## 📦 Installation

### Option 1: Docker Setup (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Metal_Info_Backend_demo
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the containers**
   ```bash
   make docker-up
   # Or: docker-compose up -d
   ```

4. **Check logs**
   ```bash
   make docker-logs
   # Or: docker-compose logs -f
   ```

The application will be available at `http://localhost:8000`

### Option 2: Local Setup

1. **Install Poetry**
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Install dependencies**
   ```bash
   make install
   # Or: poetry install
   ```

3. **Set up PostgreSQL database**
   - Create a PostgreSQL database
   - Update `.env` file with your database credentials

4. **Run migrations**
   ```bash
   make migrate
   # Or: poetry run python src/manage.py migrate
   ```

5. **Start the development server**
   ```bash
   make run-server
   # Or: poetry run python src/manage.py runserver
   ```

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Database Configuration
POSTGRES_DB=metal_prices_db
POSTGRES_USER=metal_user
POSTGRES_PASSWORD=your_secure_password
DATABASE_URL=postgresql://metal_user:your_secure_password@db:5432/metal_prices_db

# Django Configuration
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# External API
METAL_PRICES_API_URL=https://api.test.customer-app.metycle.com/api/v1/scrap-lizard/metal-prices/
METAL_PRICES_API_TIMEOUT=30

# CORS Configuration
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

## 📡 API Endpoints

### Base URL
```
http://localhost:8000/api/v1/
```

### Endpoints

#### 1. List Latest Metal Prices
```http
GET /api/v1/metal-prices/
```

**Query Parameters:**
- `symbols` (optional): Comma-separated list of metal symbols to filter

**Response:**
```json
{
  "success": true,
  "count": 12,
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
      "priceHistory": [...],
      "priceHistoryCount": 30,
      "fetchedAt": "2026-01-08T12:00:00Z",
      "createdAt": "2026-01-08T12:00:00Z"
    }
  ]
}
```

#### 2. Get Specific Metal Price
```http
GET /api/v1/metal-prices/{symbol}/
```

**Response:**
```json
{
  "success": true,
  "data": {
    "uuid": "123e4567-e89b-12d3-a456-426614174000",
    "symbol": "Tense",
    "name": "Tense",
    "priceUsd": "0.9856000000",
    ...
  }
}
```

#### 3. Fetch Metal Prices from External API
```http
POST /api/v1/metal-prices/fetch/
```

**Request Body (optional):**
```json
{
  "metals": ["Tense", "Troma"]
}
```

**Response:**
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
    }
  ]
}
```

### Supported Metals

The following metal symbols are supported:
- Aroma
- Berry
- Birch
- Candy
- Cliff
- Clove
- Elmo
- Taldon
- Tainttabor
- Tense
- Troma
- Zorba

## 🧪 Testing

### Run All Tests
```bash
make test
# Or: poetry run pytest
```

### Run Tests with Coverage
```bash
make test-cov
# Or: poetry run pytest --cov=src --cov-report=html
```

### Run Specific Test File
```bash
poetry run pytest src/metal_prices/tests/test_models.py
```

### Run Tests in Docker
```bash
make docker-test
# Or: docker-compose exec web poetry run pytest
```

## 📝 Code Quality

### Linting
```bash
make lint
# Or: poetry run ruff check src/
```

### Formatting
```bash
make format
# Or: poetry run ruff format src/
```

### Pre-commit Hooks
```bash
# Install pre-commit hooks
poetry run pre-commit install

# Run on all files
make pre-commit
# Or: poetry run pre-commit run --all-files
```

## 🗄️ Database

### Create Migrations
```bash
make makemigrations
# Or: poetry run python src/manage.py makemigrations
```

### Apply Migrations
```bash
make migrate
# Or: poetry run python src/manage.py migrate
```

### Open Django Shell
```bash
make shell
# Or: poetry run python src/manage.py shell
```

## 📊 Admin Interface

Access the Django admin interface at `http://localhost:8000/admin/`

To create a superuser:
```bash
# Local
poetry run python src/manage.py createsuperuser

# Docker
docker-compose exec web python src/manage.py createsuperuser
```

## 🏗️ Project Structure

```
Metal_Info_Backend_demo/
├── src/
│   ├── config/                 # Django settings and configuration
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   ├── shared/                 # Reusable utilities
│   │   ├── models.py          # Base models (UUIDTimeStampedAbstractModel)
│   │   └── mixins.py          # DRF mixins (CamelSnakeCaseMixin)
│   ├── metal_prices/          # Metal prices app
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── serializers.py
│   │   │       ├── services.py    # Business logic
│   │   │       ├── views.py
│   │   │       └── urls.py
│   │   ├── models/
│   │   │   └── metal_price.py
│   │   ├── tests/
│   │   │   ├── conftest.py        # Pytest fixtures
│   │   │   ├── factories.py       # Factory Boy factories
│   │   │   ├── test_models.py
│   │   │   ├── test_services.py
│   │   │   └── api/v1/
│   │   │       └── test_views.py
│   │   ├── admin.py
│   │   └── apps.py
│   └── manage.py
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── Makefile
├── .env.example
├── .gitignore
└── README.md
```

## 🔄 Development Workflow

1. **Start the development environment**
   ```bash
   make docker-up
   ```

2. **Make code changes**

3. **Run tests**
   ```bash
   make test
   ```

4. **Check code quality**
   ```bash
   make lint
   make format
   ```

5. **Create migrations if models changed**
   ```bash
   docker-compose exec web python src/manage.py makemigrations
   ```

6. **Apply migrations**
   ```bash
   docker-compose exec web python src/manage.py migrate
   ```

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Stop containers
make docker-down

# Check what's using port 8000
lsof -i :8000

# Kill the process or change the port in docker-compose.yml
```

### Database Connection Issues
```bash
# Check database logs
docker-compose logs db

# Restart database container
docker-compose restart db
```

### Reset Database
```bash
# Stop containers
make docker-down

# Remove volumes
docker-compose down -v

# Start fresh
make docker-up
```

## 📚 Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Factory Boy Documentation](https://factoryboy.readthedocs.io/)

## 📄 License

[Add your license here]

## 👥 Contributors

[Add contributors here]

## 🙏 Acknowledgments

- Built following Metycle backend patterns and standards
- External API: Metycle Metal Prices API
