import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from datetime import datetime, timezone, timedelta

from app.main import app
from app.database import get_db, Base
from app.models import Job, Employer, Category, EmployerAccount
from app.auth import get_password_hash, serializer
from app.config import settings


def get_test_csrf_token():
    """Get a proper CSRF token for testing"""
    return serializer.dumps("csrf_token")


# Test database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a fresh database for each test"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop all tables
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database session"""
    with TestClient(app, follow_redirects=False) as test_client:
        yield test_client


@pytest.fixture
def admin_session(client: TestClient) -> dict:
    """Create an admin session for testing"""
    response = client.post("/admin/login", data={
        "username": settings.admin_username,
        "password": settings.admin_password,
        "csrf_token": get_test_csrf_token()
    })
    return response.cookies


@pytest.fixture
def employer_account(db: Session) -> EmployerAccount:
    """Create a test employer account"""
    employer = EmployerAccount(
        email="test@company.com",
        password_hash=get_password_hash("testpassword"),
        company_name="Test Company",
        contact_name="Test Contact",
        phone="123-456-7890",
        website="https://testcompany.com",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db.add(employer)
    db.commit()
    db.refresh(employer)
    return employer


@pytest.fixture
def employer_session(client: TestClient, employer_account: EmployerAccount) -> dict:
    """Create an employer session for testing"""
    response = client.post("/employer/login", data={
        "email": employer_account.email,
        "password": "testpassword",
        "csrf_token": get_test_csrf_token()
    })
    return response.cookies


@pytest.fixture
def category(db: Session) -> Category:
    """Create a test category"""
    category = Category(
        name="Software Development",
        slug="software-development",
        description="Software development jobs",
        created_at=datetime.now(timezone.utc)
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@pytest.fixture
def employer(db: Session, employer_account: EmployerAccount) -> Employer:
    """Create a test employer"""
    employer = Employer(
        name="Test Company",
        website="https://testcompany.com",
        description="A test company",
        account_id=employer_account.id,
        created_at=datetime.now(timezone.utc)
    )
    db.add(employer)
    db.commit()
    db.refresh(employer)
    return employer


@pytest.fixture
def published_job(db: Session, employer: Employer, category: Category) -> Job:
    """Create a published test job"""
    job = Job(
        title="Senior Python Developer",
        description="We are looking for a senior Python developer...",
        tags="python,django,fastapi",
        salary_min=80000,
        salary_max=120000,
        salary_currency="USD",
        apply_url="https://apply.example.com",
        employer_id=employer.id,
        employer_account_id=employer.account_id,
        category_id=category.id,
        status="published",
        created_at=datetime.now(timezone.utc),
        published_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc).replace(tzinfo=timezone.utc) + timedelta(days=30),
        payment_completed=True,
        payment_amount=1000
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@pytest.fixture
def draft_job(db: Session, employer: Employer, category: Category) -> Job:
    """Create a draft test job"""
    job = Job(
        title="Junior Developer",
        description="We are looking for a junior developer...",
        tags="javascript,react",
        salary_min=50000,
        salary_max=70000,
        salary_currency="USD",
        apply_url="https://apply.example.com",
        employer_id=employer.id,
        employer_account_id=employer.account_id,
        category_id=category.id,
        status="draft",
        created_at=datetime.now(timezone.utc),
        payment_amount=1000  # Add payment amount for testing
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


# Mock CSRF token for testing
@pytest.fixture(autouse=True)
def mock_csrf_token(monkeypatch):
    """Mock CSRF token generation for consistent testing"""
    def mock_generate_csrf_token():
        return serializer.dumps("csrf_token")
    
    from app.auth import generate_csrf_token
    monkeypatch.setattr("app.auth.generate_csrf_token", mock_generate_csrf_token)


# Mock Stripe for testing
@pytest.fixture(autouse=True)
def mock_stripe(monkeypatch):
    """Mock Stripe API calls for testing"""
    class MockStripe:
        def __init__(self):
            self.payment_intents = {}
            self.sessions = {}
        
        def PaymentIntent_create(self, **kwargs):
            payment_intent_id = f"pi_test_{len(self.payment_intents) + 1}"
            self.payment_intents[payment_intent_id] = {
                "id": payment_intent_id,
                "status": "succeeded",
                **kwargs
            }
            return self.payment_intents[payment_intent_id]
        
        def checkout_Session_create(self, **kwargs):
            session_id = f"cs_test_{len(self.sessions) + 1}"
            self.sessions[session_id] = {
                "id": session_id,
                "url": "https://checkout.stripe.com/test",
                **kwargs
            }
            return self.sessions[session_id]
    
    mock_stripe = MockStripe()
    monkeypatch.setattr("app.main.stripe", mock_stripe)
    return mock_stripe 