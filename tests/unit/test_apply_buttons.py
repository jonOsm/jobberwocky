import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestApplyButtons:
    """Test that Apply Now buttons point to job detail pages"""
    
    def test_apply_button_on_job_list_points_to_job_detail(self, db, employer, category):
        """Test that Apply Now button on job list page points to job detail page"""
        # Create a job with external apply URL
        from app.models import Job
        from datetime import datetime, timezone, timedelta
        
        job = Job(
            title="Test Job",
            description="Test job description",
            apply_url="https://external-company.com/apply",
            employer_id=employer.id,
            category_id=category.id,
            status="published",
            published_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30)
        )
        db.add(job)
        db.commit()
        
        # Get the job list page
        response = client.get("/")
        assert response.status_code == 200
        content = response.text
        
        # Check that Apply Now button points to job detail page, not external URL
        assert f'href="/jobs/{job.id}"' in content
        assert 'href="https://external-company.com/apply"' not in content
        assert 'Apply Now' in content
    
    def test_apply_button_on_job_detail_points_to_job_detail(self, db, employer, category):
        """Test that Apply Now button on job detail page points to job detail page"""
        # Create a job with external apply URL
        from app.models import Job
        from datetime import datetime, timezone, timedelta
        
        job = Job(
            title="Test Job",
            description="Test job description",
            apply_url="https://external-company.com/apply",
            employer_id=employer.id,
            category_id=category.id,
            status="published",
            published_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30)
        )
        db.add(job)
        db.commit()
        
        # Get the job detail page
        response = client.get(f"/jobs/{job.id}")
        assert response.status_code == 200
        content = response.text
        
        # Check that Apply Now button points to job detail page, not external URL
        assert f'href="/jobs/{job.id}"' in content
        assert 'href="https://external-company.com/apply"' not in content
        assert 'Apply Now' in content
    
    def test_apply_button_on_search_results_points_to_job_detail(self, db, employer, category):
        """Test that Apply Now button on search results points to job detail page"""
        # Create a job with external apply URL
        from app.models import Job
        from datetime import datetime, timezone, timedelta
        
        job = Job(
            title="Python Developer",
            description="Python developer job",
            apply_url="https://external-company.com/apply",
            employer_id=employer.id,
            category_id=category.id,
            status="published",
            published_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30)
        )
        db.add(job)
        db.commit()
        
        # Search for the job
        response = client.get("/", params={"search": "Python"})
        assert response.status_code == 200
        content = response.text
        
        # Check that Apply Now button points to job detail page, not external URL
        assert f'href="/jobs/{job.id}"' in content
        assert 'href="https://external-company.com/apply"' not in content
        assert 'Apply Now' in content 