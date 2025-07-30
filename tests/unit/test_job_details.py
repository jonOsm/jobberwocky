import pytest
from fastapi.testclient import TestClient
from app.models import Job, Employer, Category
from datetime import datetime, timezone


class TestJobDetails:
    """Test job detail page functionality"""
    
    def test_job_detail_page_exists_and_works(self, client: TestClient, db, employer: Employer, category: Category):
        """Test that job detail page exists and displays job information correctly"""
        # Create a job
        job = Job(
            title="Test Job",
            description="This is a test job description with **markdown** support.",
            tags="test,python",
            apply_url="https://example.com/apply",
            employer=employer,
            category=category,
            status="published",
            published_at=datetime.now(timezone.utc)
        )
        db.add(job)
        db.commit()
        
        # Try to access the job detail page
        response = client.get(f"/jobs/{job.id}")
        
        # This should fail if the route doesn't exist or has issues
        assert response.status_code == 200
        
        # Check that the job information is displayed
        content = response.text
        assert "Test Job" in content
        assert "This is a test job description" in content
        assert "<strong>markdown</strong>" in content  # Check markdown rendering
        assert employer.name in content
    
    def test_job_detail_page_returns_404_for_nonexistent_job(self, client: TestClient):
        """Test that job detail page returns 404 for non-existent jobs"""
        response = client.get("/jobs/99999")
        assert response.status_code == 404
    
    def test_job_detail_page_has_correct_structure(self, client: TestClient, db, employer: Employer, category: Category):
        """Test that job detail page has the correct HTML structure"""
        # Create a job
        job = Job(
            title="Frontend Developer",
            description="We need a **React** developer with experience in:\n\n## Requirements\n- TypeScript\n- CSS\n- Git",
            tags="react,typescript,css",
            apply_url="https://example.com/apply",
            employer=employer,
            category=category,
            status="published",
            published_at=datetime.now(timezone.utc)
        )
        db.add(job)
        db.commit()
        
        # Access the job detail page
        response = client.get(f"/jobs/{job.id}")
        assert response.status_code == 200
        
        content = response.text
        
        # Check for essential page elements
        assert "<title>" in content
        assert "Frontend Developer" in content
        assert employer.name in content
        
        # Check for job description with markdown
        assert "<strong>React</strong>" in content
        assert "<h2>Requirements</h2>" in content
        assert "<li>TypeScript</li>" in content
        assert "<li>CSS</li>" in content
        assert "<li>Git</li>" in content
        
        # Check for apply button
        assert "Apply Now" in content
        assert "https://example.com/apply" in content 