# Quick Start Guide

Get the Metal Info Backend up and running in 5 minutes!

## 🚀 Quick Setup with Docker

### 1. Prerequisites
- Docker Desktop installed and running
- Git installed

### 2. Setup Steps

```bash
# Clone the repository
cd Metal_Info_Backend_demo

# Start the application
docker-compose up --build
```

That's it! The application will:
- Build the Docker images
- Start PostgreSQL database
- Run migrations automatically
- Start the Django development server

### 3. Verify Installation

Open your browser and visit:
- API Base: http://localhost:8000/api/v1/metal-prices/
- Admin Panel: http://localhost:8000/admin/

### 4. Create Admin User (Optional)

```bash
docker-compose exec web python src/manage.py createsuperuser
```

Follow the prompts to create your admin account.

### 5. Fetch Metal Prices

Use curl or Postman to trigger a price fetch:

```bash
curl -X POST http://localhost:8000/api/v1/metal-prices/fetch/ \
  -H "Content-Type: application/json"
```

### 6. View Metal Prices

```bash
curl http://localhost:8000/api/v1/metal-prices/
```

## 🎯 Common Commands

```bash
# View logs
docker-compose logs -f

# Stop the application
docker-compose down

# Restart the application
docker-compose restart

# Run tests
docker-compose exec web poetry run pytest

# Access Django shell
docker-compose exec web python src/manage.py shell

# View database
docker-compose exec db psql -U metal_user -d metal_prices_db
```

## 🔧 Local Development (Without Docker)

If you prefer to run without Docker:

### 1. Install Dependencies

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install
```

### 2. Setup PostgreSQL

Create a PostgreSQL database and update `.env`:

```bash
POSTGRES_DB=metal_prices_db
POSTGRES_USER=metal_user
POSTGRES_PASSWORD=your_password
DATABASE_URL=postgresql://metal_user:your_password@localhost:5432/metal_prices_db
```

### 3. Run Migrations

```bash
poetry run python src/manage.py migrate
```

### 4. Start Server

```bash
poetry run python src/manage.py runserver
```

## 📚 Next Steps

- Check out the full [README.md](README.md) for detailed documentation
- Review the [API Endpoints](#api-endpoints) section
- Run the test suite: `make test`
- Explore the code structure in `src/`

## 🆘 Troubleshooting

### Port 8000 Already in Use

```bash
# Stop containers
docker-compose down

# Check what's using the port
lsof -i :8000

# Or change the port in docker-compose.yml:
# ports:
#   - "8080:8000"  # Use port 8080 instead
```

### Database Connection Issues

```bash
# Restart database
docker-compose restart db

# Check database health
docker-compose ps

# View database logs
docker-compose logs db
```

### Fresh Start

```bash
# Remove all containers and volumes
docker-compose down -v

# Rebuild and start
docker-compose up --build
```

## 🎉 Success!

You should now have:
- ✅ Django REST API running on http://localhost:8000
- ✅ PostgreSQL database running
- ✅ All migrations applied
- ✅ Ready to fetch and store metal prices

Happy coding! 🚀
