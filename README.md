# Job Board

A minimal, self-hostable job board with Stripe integration built with FastAPI, HTMX, and SQLite.

## Features

- **Public Job Board**: Browse and search job listings
- **Employer Portal**: Register, post jobs, and manage listings
- **Admin Panel**: Manage jobs, categories, and site settings
- **Payment Integration**: Stripe-powered job posting fees
- **HTMX Integration**: Dynamic UI without complex JavaScript
- **Responsive Design**: Mobile-friendly with Tailwind CSS

## Quick Start

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Run the development server**:
   ```bash
   uv run main.py
   ```

4. **Visit the application**:
   - Home: http://localhost:8000
   - Admin: http://localhost:8000/admin (admin/changeme)
   - Employer: http://localhost:8000/employer/register

## Development

### Running Tests

The project includes a comprehensive test suite with 90%+ coverage requirements.

**Run all tests with coverage**:
```bash
uv run python tests/run_tests.py
```

**Run specific test types**:
```bash
# Unit tests only
uv run python tests/run_tests.py unit

# Integration tests only  
uv run python tests/run_tests.py integration

# Quick tests without coverage
uv run python tests/run_tests.py quick
```

**Direct pytest commands**:
```bash
# All tests with coverage
uv run pytest --cov=app --cov-report=term-missing --cov-report=html:htmlcov --cov-fail-under=90

# Unit tests
uv run pytest tests/unit/ -v

# Integration tests
uv run pytest tests/integration/ -v

# Quick tests
uv run pytest --tb=short -v
```

### Test Structure

- **`tests/unit/`**: Unit tests for models, schemas, and utilities
- **`tests/integration/`**: Integration tests for API endpoints
- **`tests/conftest.py`**: Shared test fixtures and mocks
- **`tests/run_tests.py`**: Simple test runner script

### Test Coverage

The project requires 90%+ test coverage. Coverage reports are generated in `htmlcov/index.html`.

### Test Database

Tests use an in-memory SQLite database for fast, isolated test runs.

## Configuration

Key settings in `.env`:

```env
# Admin credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=changeme

# Database
DATABASE_URL=sqlite:///./job_board.db

# Stripe (sandbox for development)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_PRICE_ID=price_...

# Job settings
JOB_POST_PRICE=1000  # $10.00 in cents
JOB_EXPIRY_DAYS=30
REFUND_WINDOW_HOURS=4
```

## Project Structure

```
job_board/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── models.py        # SQLAlchemy models
│   ├── schemas.py       # Pydantic schemas
│   ├── auth.py          # Authentication utilities
│   ├── config.py        # Settings management
│   ├── database.py      # Database configuration
│   └── templates/       # Jinja2 templates
├── tests/               # Test suite
├── requirements/        # Feature requirements
├── main.py             # Development server
├── pyproject.toml      # Project configuration
└── README.md
```
