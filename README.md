# Job Board - FastAPI + HTMX

A minimal, self-hostable job board with Stripe integration built with FastAPI and HTMX.

## Features

- ✅ **CRUD for Jobs, Employers, Categories** - Full admin interface
- ✅ **Admin Authentication** - Single super-user with environment variables
- ✅ **Stripe Checkout Integration** - Pay-to-publish job posts
- ✅ **HTMX-powered Search & Filtering** - Real-time search with tags and categories
- ✅ **Auto-archive after 30 days** - Automatic job expiration
- ✅ **SEO Optimized** - Sitemap.xml + Google JobPosting schema
- ✅ **JSON Feed** - `/jobs/feed.json` for meta-site integration
- ✅ **Modern UI** - Tailwind CSS with responsive design
- ✅ **Security** - CSRF protection, input validation
- ✅ **Accessibility** - WCAG 2.1 AA compliant

## Quick Start

### 1. Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

### 2. Environment Setup

Copy the example environment file and configure it:

```bash
cp env.example .env
```

Edit `.env` with your settings:

```env
# Admin credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password

# Stripe configuration (get from Stripe dashboard)
STRIPE_SECRET_KEY=sk_test_your_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
STRIPE_PRICE_ID=price_your_product_id
```

### 3. Run the Application

```bash
# Using uv
uv run main.py

# Or directly with uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000` to see the job board!

## Admin Interface

Access the admin dashboard at `/admin` with the credentials from your `.env` file.

### Admin Features:
- Create, edit, and manage job postings
- View job statistics and status
- Manage employers and categories
- Publish/expire jobs with one click

## API Endpoints

### Public Endpoints
- `GET /` - Home page with job listings and search
- `GET /jobs/{job_id}` - Job detail page with SEO schema
- `GET /jobs/feed.json` - JSON feed of published jobs
- `GET /sitemap.xml` - XML sitemap for SEO

### Admin Endpoints
- `GET /admin` - Admin dashboard (requires auth)
- `GET /admin/jobs/new` - New job form
- `POST /admin/jobs/new` - Create job
- `GET /admin/jobs/{job_id}` - Edit job form
- `PATCH /admin/jobs/{job_id}` - Update job

### Stripe Integration
- `POST /stripe/create-checkout-session` - Create payment session
- `POST /stripe/webhook` - Handle Stripe webhooks

## Database Schema

### Jobs Table
- `id` - Primary key
- `title` - Job title
- `description` - Job description (supports markdown)
- `tags` - Comma-separated tags
- `salary_min/max` - Salary range
- `apply_url` - Application URL
- `status` - draft/published/expired
- `created_at/published_at/expires_at` - Timestamps
- `stripe_payment_intent_id` - Stripe payment tracking

### Employers Table
- `id` - Primary key
- `name` - Company name
- `website` - Company website
- `description` - Company description

### Categories Table
- `id` - Primary key
- `name` - Category name
- `slug` - URL-friendly slug
- `description` - Category description

## HTMX Features

The application uses HTMX for dynamic interactions:

- **Real-time search** - Search jobs as you type
- **Form validation** - Client-side validation with server feedback
- **Status updates** - Update job status without page reload
- **Loading indicators** - Visual feedback during requests

## Stripe Integration

### Setup
1. Create a Stripe account
2. Create a product with a price (e.g., "Job Post" for $10)
3. Configure webhook endpoint: `https://yourdomain.com/stripe/webhook`
4. Update environment variables with your Stripe keys

### Payment Flow
1. Admin creates job (draft status)
2. Job is published via Stripe Checkout
3. Payment success triggers job publication
4. Job expires after 30 days

## Deployment

### Render
```yaml
# render.yaml
services:
  - type: web
    name: job-board
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        value: postgresql://...
```

### Railway
```json
// railway.json
{
  "build": {
    "builder": "nixpacks"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/",
    "healthcheckTimeout": 300
  }
}
```

### Fly.io
```toml
# fly.toml
[app]
name = "job-board"

[build]

[env]
PORT = "8080"

[http_service]
internal_port = 8080
force_https = true
auto_stop_machines = true
auto_start_machines = true
min_machines_running = 0

[[http_service.checks]]
grace_period = "10s"
interval = "30s"
method = "GET"
timeout = "5s"
path = "/"
```

## Development

### Running Tests
```bash
uv run pytest
```

### Code Formatting
```bash
uv run black .
uv run isort .
```

### Type Checking
```bash
uv run mypy .
```

## Configuration Options

| Setting | Default | Description |
|---------|---------|-------------|
| `SALARY_RANGE_REQUIRED` | `true` | Require salary range for job posts |
| `JOB_EXPIRY_DAYS` | `30` | Days until job auto-expires |
| `JOB_POST_PRICE` | `1000` | Price in cents ($10.00) |

## Security Features

- **CSRF Protection** - All forms protected with CSRF tokens
- **Input Validation** - Pydantic schemas validate all inputs
- **SQL Injection Protection** - SQLAlchemy ORM with parameterized queries
- **XSS Protection** - Jinja2 auto-escaping
- **Authentication** - HTTP Basic Auth for admin access

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation in `/docs`
- Review the FastAPI and HTMX documentation

---

Built with ❤️ using FastAPI, HTMX, and Tailwind CSS
