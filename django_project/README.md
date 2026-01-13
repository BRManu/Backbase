# MyCurrency Project

A robust and resilient currency exchange rate platform built with Django and Docker. This project retrieves exchange rates from external providers (CurrencyBeacon), stores them efficiently, and exposes a REST API for current rates, historical data, and currency conversion.

## Features

*   **Resilient Provider System**: Automatically fails over to a Mock provider if the main API (CurrencyBeacon) is unavailable or rate-limited.
*   **Async Historical Loader**: efficiently loads thousands of historical records using `asyncio` and `aiohttp`.
*   **REST API (v1)**: Fully documented API with Swagger/OpenAPI support.
*   **Dockerized**: Easy setup and deployment with Docker Compose.
*   **Comprehensive Testing**: Includes a full suite of tests (models, API, services) using `pytest`.

## Prerequisites

*   Docker && Docker Compose

## Setup & Running

1.  **Clone the repository** (if you haven't already).

2.  **Environment Configuration**:
    The project uses `docker-compose.yml` for configuration. The `CURRENCY_BEACON_API_KEY` is already configured in `docker-compose.yml`.

3.  **Build and Start**:
    ```bash
    docker-compose up --build -d
    ```

4.  **Access the Application**:
    *   **API Root**: [http://localhost:8000/api/v1/](http://localhost:8000/api/v1/)
    *   **Swagger UI**: [http://localhost:8000/api/schema/swagger-ui/](http://localhost:8000/api/schema/swagger-ui/)
    *   **Django Admin**: [http://localhost:8000/admin/](http://localhost:8000/admin/) (User/Pass: `admin`/`admin` - *Note: You may need to create a superuser first if not pre-seeded*)

## Common Commands

### Create Superuser
```bash
docker-compose exec web python manage.py createsuperuser
```

### Run Tests
The project includes a comprehensive test suite.
```bash
docker-compose exec web pytest MyCurrency/tests/ -v
```

### Load Historical Data
Load data asynchronously from the CLI.
```bash
# Example: Load data for Jan 2024
docker-compose exec web python manage.py load_historical --source EUR --targets USD,GBP,CHF --from 2024-01-01 --to 2024-01-31
```

### Interact with Shell
```bash
docker-compose exec web python manage.py shell
```

## API Endpoints (v1)

*   `GET /api/v1/currencies/` - List supported currencies.
*   `GET /api/v1/rates/?source_currency=EUR&date_from=2024-01-01&date_to=2024-01-07` - Get historical rates.
*   `POST /api/v1/convert/` - Convert an amount between currencies.
    *   Body: `{"source_currency": "EUR", "amount": 100, "exchanged_currency": "USD"}`

## Architecture

*   **Backend**: Python 3.11, Django 5.x, Django Rest Framework.
*   **Database**: PostgreSQL 15.
*   **Async**: `aiohttp` and `asyncio` for high-performance data fetching.
*   **Testing**: `pytest` and `pytest-django`.
