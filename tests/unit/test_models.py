import pytest
from datetime import datetime, timedelta, timezone
from app.models import Job, Employer, Category, EmployerAccount
from app.config import settings


class TestJobProperties:
    """Test Job model properties and business logic"""
    
    def test_tag_list_with_tags(self):
        """Test tag_list property with comma-separated tags"""
        job = Job(tags="python,django,fastapi")
        assert job.tag_list == ["python", "django", "fastapi"]
    
    def test_tag_list_without_tags(self):
        """Test tag_list property with no tags"""
        job = Job(tags=None)
        assert job.tag_list == []
    
    def test_tag_list_with_empty_string(self):
        """Test tag_list property with empty string"""
        job = Job(tags="")
        assert job.tag_list == []
    
    def test_tag_list_with_spaces(self):
        """Test tag_list property handles spaces correctly"""
        job = Job(tags=" python , django , fastapi ")
        assert job.tag_list == ["python", "django", "fastapi"]
    
    def test_is_expired_future_date(self):
        """Test is_expired with future expiry date"""
        future_date = datetime.now(timezone.utc) + timedelta(days=1)
        job = Job(expires_at=future_date)
        assert job.is_expired is False
    
    def test_is_expired_past_date(self):
        """Test is_expired with past expiry date"""
        past_date = datetime.now(timezone.utc) - timedelta(days=1)
        job = Job(expires_at=past_date)
        assert job.is_expired is True
    
    def test_is_expired_no_expiry_date(self):
        """Test is_expired with no expiry date"""
        job = Job(expires_at=None)
        assert job.is_expired is False
    
    def test_is_expired_naive_datetime(self):
        """Test is_expired with timezone-naive datetime (backward compatibility)"""
        naive_future = datetime.now() + timedelta(days=1)
        job = Job(expires_at=naive_future)
        assert job.is_expired is False
        
        naive_past = datetime.now() - timedelta(days=1)
        job = Job(expires_at=naive_past)
        assert job.is_expired is True
    
    def test_can_refund_within_window(self):
        """Test can_refund within refund window"""
        published_at = datetime.now(timezone.utc) - timedelta(hours=2)
        job = Job(
            status="published",
            published_at=published_at
        )
        assert job.can_refund is True
    
    def test_can_refund_outside_window(self):
        """Test can_refund outside refund window"""
        published_at = datetime.now(timezone.utc) - timedelta(hours=settings.refund_window_hours + 1)
        job = Job(
            status="published",
            published_at=published_at
        )
        assert job.can_refund is False
    
    def test_can_refund_draft_job(self):
        """Test can_refund for draft job"""
        job = Job(
            status="draft",
            published_at=datetime.now(timezone.utc)
        )
        assert job.can_refund is False
    
    def test_can_refund_no_published_at(self):
        """Test can_refund with no published_at date"""
        job = Job(status="published")
        assert job.can_refund is False
    
    def test_can_refund_naive_datetime(self):
        """Test can_refund with timezone-naive datetime (backward compatibility)"""
        published_at = datetime.now() - timedelta(hours=2)
        job = Job(
            status="published",
            published_at=published_at
        )
        assert job.can_refund is True
    
    def test_to_dict(self):
        """Test to_dict method"""
        employer = Employer(name="Test Company")
        category = Category(name="Software Development")
        
        job = Job(
            id=1,
            title="Test Job",
            description="Test description",
            tags="python,django",
            salary_min=50000,
            salary_max=70000,
            salary_currency="USD",
            apply_url="https://apply.example.com",
            status="published",
            created_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
            published_at=datetime(2023, 1, 2, tzinfo=timezone.utc),
            expires_at=datetime(2023, 2, 1, tzinfo=timezone.utc),
            employer=employer,
            category=category
        )
        
        result = job.to_dict()
        
        assert result["id"] == 1
        assert result["title"] == "Test Job"
        assert result["description"] == "Test description"
        assert result["tags"] == "python,django"
        assert result["salary_min"] == 50000
        assert result["salary_max"] == 70000
        assert result["salary_currency"] == "USD"
        assert result["apply_url"] == "https://apply.example.com"
        assert result["status"] == "published"
        assert result["employer_name"] == "Test Company"
        assert result["category_name"] == "Software Development"
        assert result["created_at"] == "2023-01-01T00:00:00+00:00"
        assert result["published_at"] == "2023-01-02T00:00:00+00:00"
        assert result["expires_at"] == "2023-02-01T00:00:00+00:00"
        assert "can_refund" in result


class TestJobInitialization:
    """Test Job model initialization logic"""
    
    def test_init_published_job_sets_dates(self):
        """Test that published jobs get published_at and expires_at set"""
        job = Job(status="published")
        
        # Check that dates are set (within reasonable time)
        now = datetime.now(timezone.utc)
        assert job.published_at is not None
        assert job.expires_at is not None
        assert abs((job.published_at - now).total_seconds()) < 5  # Within 5 seconds
        assert abs((job.expires_at - now - timedelta(days=settings.job_expiry_days)).total_seconds()) < 5
    
    def test_init_draft_job_no_dates(self):
        """Test that draft jobs don't get published_at and expires_at set"""
        job = Job(status="draft")
        assert job.published_at is None
        assert job.expires_at is None
    
    def test_init_published_job_with_existing_dates(self):
        """Test that published jobs with existing dates don't get overwritten"""
        existing_published = datetime(2023, 1, 1, tzinfo=timezone.utc)
        existing_expires = datetime(2023, 2, 1, tzinfo=timezone.utc)
        
        job = Job(
            status="published",
            published_at=existing_published,
            expires_at=existing_expires
        )
        
        assert job.published_at == existing_published
        assert job.expires_at == existing_expires 