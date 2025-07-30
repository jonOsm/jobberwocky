# Jobberwocky

A modern, self-hostable job board with Stripe payment integration. Built with FastAPI, HTMX, and SQLite for simplicity and performance.

> **⚠️ Early Development**: This project is in active development and seeking feedback. Please report issues and share your experience!

## Purpose

Jobberwocky is designed for organizations, communities, or individuals who want to host their own job board without the complexity of enterprise solutions. It provides:

- **Simple Job Posting**: Employers can easily post jobs with integrated payments
- **Clean Job Discovery**: Job seekers can browse and search listings efficiently  
- **Admin Management**: Complete control over jobs, employers, and site settings
- **Payment Processing**: Integrated Stripe payments for job posting fees
- **Modern UI**: Responsive design with HTMX for dynamic interactions

## Architecture

### System Overview

```mermaid
graph TB
    subgraph "Frontend"
        UI[Web Interface]
    end
    
    subgraph "Backend"
        API[FastAPI App]
        AUTH[Authentication]
        PAY[Payment Handler]
    end
    
    subgraph "Data"
        DB[(SQLite DB)]
    end
    
    subgraph "External"
        STRIPE[Stripe API]
    end
    
    UI --> API
    API --> AUTH
    API --> PAY
    API --> DB
    PAY --> STRIPE
```

### User Flow

```mermaid
flowchart LR
    A[User] --> B{User Type}
    B -->|Public| C[View Jobs]
    B -->|Employer| D[Manage Jobs]
    B -->|Admin| E[Admin Panel]
    
    D --> F[Create Job]
    F --> G[Pay with Stripe]
    G --> H[Job Published]
    
    C --> I[Search Jobs]
    I --> J[Apply to Job]
```

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

1. **Clone and install dependencies**:
   ```bash
   git clone <repository-url>
   cd job_board
   uv sync
   ```

2. **Set up environment**:
   ```bash
   cp env.example .env
   # Edit .env with your settings (see Configuration section)
   ```

3. **Run the development server**:
   ```bash
   uv run main.py
   ```

4. **Access the application**:
   - **Home**: http://localhost:8000
   - **Admin**: http://localhost:8000/admin (admin/changeme)
   - **Employer Portal**: http://localhost:8000/employer/register

## Configuration

### Environment Variables

Create a `.env` file with the following settings:

```env
# Database
DATABASE_URL=sqlite:///./job_board.db

# Admin credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=changeme
SECRET_KEY=your-secret-key-change-in-production

# Stripe Configuration (sandbox for development)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Application Settings
JOB_POST_PRICE=1000  # $10.00 in cents
JOB_EXPIRY_DAYS=30
REFUND_WINDOW_HOURS=4
SALARY_RANGE_REQUIRED=true
EMPLOYER_REGISTRATION_ENABLED=true
MAX_JOBS_PER_EMPLOYER=  # Leave empty for unlimited
```

### Stripe Setup

1. Create a [Stripe account](https://stripe.com)
2. Get your API keys from the Stripe Dashboard
3. Set up a webhook endpoint pointing to `/stripe/webhook`
4. Update your `.env` file with the keys

### Database Setup

The application uses SQLite by default. For production, you can switch to PostgreSQL:

```env
DATABASE_URL=postgresql://user:password@localhost/jobberwocky
```

> **⚠️ PostgreSQL Support**: PostgreSQL integration needs testing. Please report any issues when using PostgreSQL in production.

## Development

### Running Tests

```bash
# Run all tests with coverage
uv run python tests/run_tests.py

# Run specific test types
uv run python tests/run_tests.py unit
uv run python tests/run_tests.py integration
```

### Project Structure

```
job_board/
├── app/
│   ├── main.py          # FastAPI application
│   ├── models.py        # SQLAlchemy models
│   ├── auth.py          # Authentication utilities
│   ├── config.py        # Settings management
│   ├── database.py      # Database configuration
│   ├── utils.py         # Utility functions
│   └── templates/       # Jinja2 templates
├── tests/               # Test suite
├── migrations/          # Database migrations
├── scripts/             # Utility scripts
└── requirements/        # Feature requirements
```

## Features

### For Job Seekers
- Browse published job listings
- Search by keywords, categories, and tags
- View detailed job descriptions with markdown support
- Access JSON feed for integrations

### For Employers
- Register and manage employer accounts
- Create and edit job postings
- Integrated payment processing with Stripe
- Dashboard to manage all job listings
- Refund requests within time window

### For Administrators
- Complete job and employer management
- Category and site settings control
- Payment monitoring and refund processing
- User account management

## Security

- **Session-based authentication** for employers and admins
- **CSRF protection** on all forms
- **Input validation** and sanitization
- **Secure cookie handling**
- **Stripe webhook verification** for payment security

## Deployment

### Production Considerations

1. **Use HTTPS**: Set up SSL/TLS certificates
2. **Database**: Consider PostgreSQL for production
3. **Environment**: Use proper environment variables
4. **Monitoring**: Set up logging and monitoring
5. **Backup**: Regular database backups

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install uv && uv sync --frozen

EXPOSE 8000
CMD ["uv", "run", "main.py"]
```

## Contributing

We welcome contributions! Please see our [ROADMAP](ROADMAP.md) for planned features and areas where help is needed.

### How to Contribute

1. **Check the roadmap**: Review [ROADMAP.md](ROADMAP.md) for planned features
2. **Fork the repository**: Create your own fork
3. **Create a feature branch**: Work on your changes
4. **Add tests**: Ensure new functionality is tested
5. **Submit a pull request**: Include a clear description of your changes

### Areas Needing Help

- Frontend improvements (HTMX, CSS)
- Backend optimizations (FastAPI, SQLAlchemy)
- Documentation and tutorials
- Testing and bug fixes
- Feature development

### Development Guidelines

- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass before submitting

## License

This project is dual-licensed:

### Open Source License
Jobberwocky is released under the **GNU Affero General Public License v3.0 (AGPL-3.0)**. This means:

- ✅ You can use, modify, and distribute the software
- ✅ You can use it for commercial purposes
- ✅ You must share any modifications you make
- ✅ If you run it as a network service, you must provide source code to users

### Commercial License
For organizations that need:
- Proprietary modifications without sharing requirements
- Commercial support and consulting
- Premium features and integrations
- Warranty and indemnification

Contact us for commercial licensing options.

### License Compliance
When using the AGPL-3.0 version:
- Include the full license text
- State any changes you made
- Provide source code access to network users
- Include copyright notices

For full license text, see [LICENSE](LICENSE) file.
