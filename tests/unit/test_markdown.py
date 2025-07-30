import pytest
from fastapi.testclient import TestClient
from app.models import Job, Employer, Category
from datetime import datetime, timezone


class TestMarkdownRendering:
    """Test markdown rendering for job descriptions"""
    
    def test_job_list_page_renders_markdown_description(self, client: TestClient, db, employer: Employer, category: Category):
        """Test that job descriptions with markdown are properly rendered in the job list"""
        # Create a job with markdown description
        job = Job(
            title="Python Developer",
            description="**Strong Python skills** required.\n\n- Experience with FastAPI\n- Knowledge of SQLAlchemy\n- Familiar with **HTMX**",
            tags="python,fastapi,htmx",
            apply_url="https://example.com/apply",
            employer=employer,
            category=category,
            status="published",
            published_at=datetime.now(timezone.utc)
        )
        db.add(job)
        db.commit()
        
        # Get the job list page
        response = client.get("/")
        
        assert response.status_code == 200
        
        # Check that markdown is rendered as HTML
        content = response.text
        assert "<strong>Strong Python skills</strong>" in content
        assert "<ul>" in content
        assert "<li>Experience with FastAPI</li>" in content
        assert "<li>Knowledge of SQLAlchemy</li>" in content
        assert "<li>Familiar with <strong>HTMX</strong></li>" in content
    
    def test_search_results_renders_markdown_description(self, client: TestClient, db, employer: Employer, category: Category):
        """Test that job descriptions with markdown are properly rendered in search results"""
        # Create a job with markdown description
        job = Job(
            title="Frontend Developer",
            description="Looking for a **React** developer.\n\n## Requirements:\n- TypeScript experience\n- **CSS** skills\n- Git workflow",
            tags="react,typescript,css",
            apply_url="https://example.com/apply",
            employer=employer,
            category=category,
            status="published",
            published_at=datetime.now(timezone.utc)
        )
        db.add(job)
        db.commit()
        
        # Search for the job
        response = client.get("/search?q=react")
        
        assert response.status_code == 200
        
        # Check that markdown is rendered as HTML
        content = response.text
        assert "<strong>React</strong>" in content
        assert "<h2>Requirements:</h2>" in content
        assert "<li>TypeScript experience</li>" in content
        assert "<li><strong>CSS</strong> skills</li>" in content
        assert "<li>Git workflow</li>" in content
    
    def test_plain_text_description_remains_unchanged(self, client: TestClient, db, employer: Employer, category: Category):
        """Test that plain text descriptions without markdown are displayed as-is"""
        # Create a job with plain text description
        job = Job(
            title="Data Analyst",
            description="We are looking for a data analyst with strong SQL skills and experience with Python pandas library.",
            tags="sql,python,pandas",
            apply_url="https://example.com/apply",
            employer=employer,
            category=category,
            status="published",
            published_at=datetime.now(timezone.utc)
        )
        db.add(job)
        db.commit()
        
        # Get the job list page
        response = client.get("/")
        
        assert response.status_code == 200
        
        # Check that plain text is displayed as-is (no HTML tags)
        content = response.text
        assert "We are looking for a data analyst with strong SQL skills and experience with Python pandas library." in content
        assert "<strong>" not in content
        assert "<ul>" not in content
        assert "<h2>" not in content
    
    def test_markdown_special_characters_are_escaped(self, client: TestClient, db, employer: Employer, category: Category):
        """Test that HTML special characters in markdown are properly escaped"""
        # Create a job with markdown that contains HTML-like content
        job = Job(
            title="Security Engineer",
            description="Looking for someone to work with **<script>alert('xss')</script>** and other security tools.",
            tags="security,python",
            apply_url="https://example.com/apply",
            employer=employer,
            category=category,
            status="published",
            published_at=datetime.now(timezone.utc)
        )
        db.add(job)
        db.commit()
        
        # Get the job list page
        response = client.get("/")
        
        assert response.status_code == 200
        
        # Check that HTML is escaped in the job description context
        content = response.text
        # Look for the escaped script tag in the full content
        assert "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;" in content
        # Make sure the actual script tags are not in the content
        assert "<script>alert('xss')</script>" not in content
    
    def test_job_detail_page_renders_markdown_description(self, client: TestClient, db, employer: Employer, category: Category):
        """Test that job descriptions with markdown are properly rendered on the job detail page"""
        # Create a job with markdown description
        job = Job(
            title="DevOps Engineer",
            description="We need a **DevOps engineer** with experience in:\n\n## Required Skills:\n- **Docker** and Kubernetes\n- AWS or Azure\n- CI/CD pipelines\n- Monitoring tools",
            tags="devops,docker,kubernetes",
            apply_url="https://example.com/apply",
            employer=employer,
            category=category,
            status="published",
            published_at=datetime.now(timezone.utc)
        )
        db.add(job)
        db.commit()
        
        # Get the job detail page
        response = client.get(f"/jobs/{job.id}")
        
        assert response.status_code == 200
        
        # Check that markdown is rendered as HTML
        content = response.text
        assert "<strong>DevOps engineer</strong>" in content
        assert "<h2>Required Skills:</h2>" in content
        assert "<li><strong>Docker</strong> and Kubernetes</li>" in content
        assert "<li>AWS or Azure</li>" in content
        assert "<li>CI/CD pipelines</li>" in content
        assert "<li>Monitoring tools</li>" in content
    
    def test_markdown_headers_are_properly_styled(self, client: TestClient, db, employer: Employer, category: Category):
        """Test that markdown headers are properly styled with appropriate HTML tags"""
        # Create a job with markdown headers
        job = Job(
            title="Technical Writer",
            description="# Main Title\n\n## Section 1\nThis is section 1.\n\n### Subsection\nThis is a subsection.\n\n## Section 2\nThis is section 2.",
            tags="writing,technical,documentation",
            apply_url="https://example.com/apply",
            employer=employer,
            category=category,
            status="published",
            published_at=datetime.now(timezone.utc)
        )
        db.add(job)
        db.commit()
        
        # Get the job detail page
        response = client.get(f"/jobs/{job.id}")
        
        assert response.status_code == 200
        
        # Check that headers are rendered as proper HTML tags
        content = response.text
        assert "<h1>Main Title</h1>" in content
        assert "<h2>Section 1</h2>" in content
        assert "<h3>Subsection</h3>" in content
        assert "<h2>Section 2</h2>" in content 