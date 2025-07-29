import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from app.schemas import (
    JobCreate, JobUpdate, JobSearchParams, JobResponse,
    EmployerCreate, CategoryCreate,
    EmployerAccountCreate, EmployerAccountLogin, EmployerAccountResponse,
    RefundRequest
)


class TestJobCreate:
    """Test JobCreate schema validation"""
    
    def test_valid_job_create(self):
        """Test valid job creation data"""
        data = {
            "title": "Senior Python Developer",
            "description": "We are looking for a senior Python developer...",
            "tags": "python,django,fastapi",
            "salary_min": 80000,
            "salary_max": 120000,
            "salary_currency": "USD",
            "apply_url": "https://apply.example.com",
            "employer_id": 1,
            "category_id": 1
        }
        
        job = JobCreate(**data)
        assert job.title == "Senior Python Developer"
        assert job.description == "We are looking for a senior Python developer..."
        assert job.tags == "python,django,fastapi"
        assert job.salary_min == 80000
        assert job.salary_max == 120000
        assert job.salary_currency == "USD"
        assert job.apply_url == "https://apply.example.com"
        assert job.employer_id == 1
        assert job.category_id == 1
    
    def test_job_create_missing_required_fields(self):
        """Test job creation with missing required fields"""
        data = {
            "title": "Senior Python Developer",
            # Missing description, apply_url, employer_id
        }
        
        with pytest.raises(ValidationError) as exc_info:
            JobCreate(**data)
        
        errors = exc_info.value.errors()
        error_fields = [error["loc"][0] for error in errors]
        assert "description" in error_fields
        assert "apply_url" in error_fields
        assert "employer_id" in error_fields
    
    def test_job_create_invalid_salary_range(self):
        """Test job creation with invalid salary range"""
        data = {
            "title": "Senior Python Developer",
            "description": "We are looking for a senior Python developer...",
            "apply_url": "https://apply.example.com",
            "employer_id": 1,
            "salary_min": 120000,
            "salary_max": 80000  # Max less than min
        }
        
        with pytest.raises(ValidationError) as exc_info:
            JobCreate(**data)
        
        errors = exc_info.value.errors()
        assert any("salary_max must be greater than salary_min" in str(error) for error in errors)
    
    def test_job_create_invalid_url(self):
        """Test job creation with invalid URL"""
        data = {
            "title": "Senior Python Developer",
            "description": "We are looking for a senior Python developer...",
            "apply_url": "not-a-valid-url",
            "employer_id": 1
        }
        
        with pytest.raises(ValidationError) as exc_info:
            JobCreate(**data)
        
        errors = exc_info.value.errors()
        assert any("apply_url" in str(error) for error in errors)


class TestJobUpdate:
    """Test JobUpdate schema validation"""
    
    def test_valid_job_update(self):
        """Test valid job update data"""
        data = {
            "title": "Updated Job Title",
            "description": "Updated description",
            "status": "published"
        }
        
        job_update = JobUpdate(**data)
        assert job_update.title == "Updated Job Title"
        assert job_update.description == "Updated description"
        assert job_update.status == "published"
    
    def test_job_update_partial(self):
        """Test job update with partial data"""
        data = {
            "title": "Updated Job Title"
        }
        
        job_update = JobUpdate(**data)
        assert job_update.title == "Updated Job Title"
        assert job_update.description is None
        assert job_update.status is None
    
    def test_job_update_invalid_status(self):
        """Test job update with invalid status"""
        data = {
            "status": "invalid_status"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            JobUpdate(**data)
        
        errors = exc_info.value.errors()
        assert any("status" in str(error) for error in errors)


class TestJobSearchParams:
    """Test JobSearchParams schema validation"""
    
    def test_valid_search_params(self):
        """Test valid search parameters"""
        data = {
            "q": "python developer",
            "category": "software-development",
            "tags": "python,django",
            "salary_min": 50000,
            "salary_max": 100000
        }
        
        params = JobSearchParams(**data)
        assert params.q == "python developer"
        assert params.category == "software-development"
        assert params.tags == "python,django"
        assert params.salary_min == 50000
        assert params.salary_max == 100000
    
    def test_search_params_empty(self):
        """Test search parameters with no filters"""
        params = JobSearchParams()
        assert params.q is None
        assert params.category is None
        assert params.tags is None
        assert params.salary_min is None
        assert params.salary_max is None


class TestEmployerAccountCreate:
    """Test EmployerAccountCreate schema validation"""
    
    def test_valid_employer_account_create(self):
        """Test valid employer account creation"""
        data = {
            "email": "test@company.com",
            "password": "securepassword123",
            "company_name": "Test Company",
            "contact_name": "John Doe",
            "phone": "123-456-7890",
            "website": "https://testcompany.com"
        }
        
        account = EmployerAccountCreate(**data)
        assert account.email == "test@company.com"
        assert account.password == "securepassword123"
        assert account.company_name == "Test Company"
        assert account.contact_name == "John Doe"
        assert account.phone == "123-456-7890"
        assert account.website == "https://testcompany.com"
    
    def test_employer_account_create_invalid_email(self):
        """Test employer account creation with invalid email"""
        data = {
            "email": "not-a-valid-email",
            "password": "securepassword123",
            "company_name": "Test Company",
            "contact_name": "John Doe"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            EmployerAccountCreate(**data)
        
        errors = exc_info.value.errors()
        assert any("email" in str(error) for error in errors)
    
    def test_employer_account_create_weak_password(self):
        """Test employer account creation with weak password"""
        data = {
            "email": "test@company.com",
            "password": "123",  # Too short
            "company_name": "Test Company",
            "contact_name": "John Doe"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            EmployerAccountCreate(**data)
        
        errors = exc_info.value.errors()
        assert any("password" in str(error) for error in errors)
    
    def test_employer_account_create_invalid_website(self):
        """Test employer account creation with invalid website"""
        data = {
            "email": "test@company.com",
            "password": "securepassword123",
            "company_name": "Test Company",
            "contact_name": "John Doe",
            "website": "not-a-valid-url"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            EmployerAccountCreate(**data)
        
        errors = exc_info.value.errors()
        assert any("website" in str(error) for error in errors)


class TestEmployerAccountLogin:
    """Test EmployerAccountLogin schema validation"""
    
    def test_valid_employer_login(self):
        """Test valid employer login data"""
        data = {
            "email": "test@company.com",
            "password": "securepassword123"
        }
        
        login = EmployerAccountLogin(**data)
        assert login.email == "test@company.com"
        assert login.password == "securepassword123"
    
    def test_employer_login_invalid_email(self):
        """Test employer login with invalid email"""
        data = {
            "email": "not-a-valid-email",
            "password": "securepassword123"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            EmployerAccountLogin(**data)
        
        errors = exc_info.value.errors()
        assert any("email" in str(error) for error in errors)


class TestRefundRequest:
    """Test RefundRequest schema validation"""
    
    def test_valid_refund_request(self):
        """Test valid refund request"""
        data = {
            "reason": "Job posted by mistake"
        }
        
        refund = RefundRequest(**data)
        assert refund.reason == "Job posted by mistake"
    
    def test_refund_request_empty_reason(self):
        """Test refund request with empty reason"""
        data = {
            "reason": ""
        }
        
        with pytest.raises(ValidationError) as exc_info:
            RefundRequest(**data)
        
        errors = exc_info.value.errors()
        assert any("reason" in str(error) for error in errors)
    
    def test_refund_request_no_reason(self):
        """Test refund request with no reason"""
        with pytest.raises(ValidationError) as exc_info:
            RefundRequest()
        
        errors = exc_info.value.errors()
        assert any("reason" in str(error) for error in errors)


class TestJobResponse:
    """Test JobResponse schema validation"""
    
    def test_valid_job_response(self):
        """Test valid job response data"""
        data = {
            "id": 1,
            "title": "Senior Python Developer",
            "description": "We are looking for a senior Python developer...",
            "tags": "python,django,fastapi",
            "salary_min": 80000,
            "salary_max": 120000,
            "salary_currency": "USD",
            "apply_url": "https://apply.example.com",
            "employer_name": "Test Company",
            "category_name": "Software Development",
            "status": "published",
            "created_at": "2023-01-01T00:00:00+00:00",
            "published_at": "2023-01-02T00:00:00+00:00",
            "expires_at": "2023-02-01T00:00:00+00:00",
            "can_refund": True
        }
        
        response = JobResponse(**data)
        assert response.id == 1
        assert response.title == "Senior Python Developer"
        assert response.status == "published"
        assert response.can_refund is True 