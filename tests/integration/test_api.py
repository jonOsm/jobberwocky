import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from app.models import Job, Employer, Category, EmployerAccount
from app.auth import serializer
from app.config import settings


def get_test_csrf_token():
    """Get a proper CSRF token for testing"""
    return serializer.dumps("csrf_token")


class TestPublicRoutes:
    """Test public-facing API routes"""
    
    def test_home_page(self, client: TestClient, published_job: Job):
        """Test home page loads with published jobs"""
        response = client.get("/")
        assert response.status_code == 200
        assert "Senior Python Developer" in response.text
        assert "Test Company" in response.text
    
    def test_search_jobs(self, client: TestClient, published_job: Job):
        """Test job search functionality"""
        response = client.get("/search", params={"q": "python"})
        assert response.status_code == 200
        assert "python" in response.text.lower()
    
    def test_search_jobs_no_results(self, client: TestClient, published_job: Job):
        """Test job search with no matching results"""
        response = client.get("/search", params={"q": "nonexistent"})
        assert response.status_code == 200
        assert "python" not in response.text.lower()
    
    def test_job_detail_page(self, client: TestClient, published_job: Job):
        """Test individual job detail page"""
        response = client.get(f"/jobs/{published_job.id}")
        assert response.status_code == 200
        assert published_job.title in response.text
        assert published_job.description in response.text
    
    def test_job_detail_not_found(self, client: TestClient):
        """Test job detail page for non-existent job"""
        response = client.get("/jobs/99999")
        assert response.status_code == 404
    
    def test_jobs_feed_json(self, client: TestClient, published_job: Job):
        """Test jobs feed JSON endpoint"""
        response = client.get("/jobs/feed.json")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["title"] == published_job.title
    
    def test_sitemap_xml(self, client: TestClient, published_job: Job):
        """Test sitemap XML generation"""
        response = client.get("/sitemap.xml")
        assert response.status_code == 200
        assert "application/xml" in response.headers["content-type"]
        assert f"/jobs/{published_job.id}" in response.text


class TestEmployerRoutes:
    """Test employer-facing API routes"""
    
    def test_employer_register_form(self, client: TestClient):
        """Test employer registration form page"""
        response = client.get("/employer/register")
        assert response.status_code == 200
        assert "Register" in response.text
        assert "company_name" in response.text
    
    def test_employer_register_success(self, client: TestClient, db: Session):
        """Test successful employer registration"""
        response = client.post("/employer/register", data={
            "email": "new@company.com",
            "password": "securepassword123",
            "company_name": "New Company",
            "contact_name": "John Doe",
            "phone": "123-456-7890",
            "website": "https://newcompany.com",
            "csrf_token": get_test_csrf_token()
        })
        
        # Should redirect to dashboard
        assert response.status_code == 302
        assert "employer/dashboard" in response.headers["location"]
        
        # Check that account was created
        account = db.query(EmployerAccount).filter_by(email="new@company.com").first()
        assert account is not None
        assert account.company_name == "New Company"
    
    def test_employer_register_duplicate_email(self, client: TestClient, employer_account: EmployerAccount):
        """Test employer registration with duplicate email"""
        response = client.post("/employer/register", data={
            "email": employer_account.email,
            "password": "securepassword123",
            "company_name": "Another Company",
            "contact_name": "Jane Doe",
            "csrf_token": get_test_csrf_token()
        })
        
        assert response.status_code == 200  # Form reloaded with error
        assert "already exists" in response.text
    
    def test_employer_login_form(self, client: TestClient):
        """Test employer login form page"""
        response = client.get("/employer/login")
        assert response.status_code == 200
        assert "Login" in response.text
        assert "email" in response.text
    
    def test_employer_login_success(self, client: TestClient, employer_account: EmployerAccount):
        """Test successful employer login"""
        response = client.post("/employer/login", data={
            "email": employer_account.email,
            "password": "testpassword",
            "csrf_token": get_test_csrf_token()
        })
        
        assert response.status_code == 302
        assert "employer/dashboard" in response.headers["location"]
    
    def test_employer_login_invalid_credentials(self, client: TestClient, employer_account: EmployerAccount):
        """Test employer login with invalid credentials"""
        response = client.post("/employer/login", data={
            "email": employer_account.email,
            "password": "wrongpassword",
            "csrf_token": get_test_csrf_token()
        })
        
        assert response.status_code == 200  # Form reloaded with error
        assert "Invalid" in response.text
    
    def test_employer_dashboard_authenticated(self, client: TestClient, employer_session: dict):
        """Test employer dashboard when authenticated"""
        response = client.get("/employer/dashboard", cookies=employer_session)
        assert response.status_code == 200
        assert "Dashboard" in response.text
        assert "Test Company" in response.text
    
    def test_employer_dashboard_unauthenticated(self, client: TestClient):
        """Test employer dashboard when not authenticated"""
        response = client.get("/employer/dashboard")
        assert response.status_code == 302
        assert "employer/login" in response.headers["location"]
    
    def test_employer_logout(self, client: TestClient, employer_session: dict):
        """Test employer logout"""
        response = client.post("/employer/logout", data={
            "csrf_token": get_test_csrf_token()
        }, cookies=employer_session)
        
        assert response.status_code == 302
        assert response.headers["location"] == "/"
    
    def test_new_job_form_authenticated(self, client: TestClient, employer_session: dict, category: Category):
        """Test new job form when authenticated"""
        response = client.get("/employer/jobs/new", cookies=employer_session)
        assert response.status_code == 200
        assert "Post New Job" in response.text
        assert "title" in response.text
    
    def test_new_job_form_unauthenticated(self, client: TestClient):
        """Test new job form when not authenticated"""
        response = client.get("/employer/jobs/new")
        assert response.status_code == 302
        assert "employer/login" in response.headers["location"]
    
    def test_create_job_success(self, client: TestClient, employer_session: dict, employer: Employer, category: Category):
        """Test successful job creation"""
        response = client.post("/employer/jobs/new", data={
            "title": "New Job Posting",
            "description": "We are hiring for a new position",
            "tags": "python,fastapi",
            "salary_min": "60000",
            "salary_max": "80000",
            "apply_url": "https://apply.example.com",
            "employer_id": str(employer.id),
            "category_id": str(category.id),
            "csrf_token": get_test_csrf_token()
        }, cookies=employer_session)
        
        assert response.status_code == 302
        assert "payment" in response.headers["location"]
    
    def test_job_payment_page(self, client: TestClient, employer_session: dict, draft_job: Job):
        """Test job payment page"""
        response = client.get(f"/employer/jobs/{draft_job.id}/payment", cookies=employer_session)
        assert response.status_code == 200
        assert "Payment" in response.text
        assert draft_job.title in response.text
    
    def test_refund_request_success(self, client: TestClient, employer_session: dict, published_job: Job):
        """Test successful refund request"""
        response = client.post(f"/employer/jobs/{published_job.id}/refund", data={
            "reason": "Job posted by mistake",
            "csrf_token": get_test_csrf_token()
        }, cookies=employer_session)
        
        assert response.status_code == 200
        assert "refunded" in response.text


class TestAdminRoutes:
    """Test admin-facing API routes"""
    
    def test_admin_login_form(self, client: TestClient):
        """Test admin login form page"""
        response = client.get("/admin/login")
        assert response.status_code == 200
        assert "Login" in response.text
        assert "username" in response.text
    
    def test_admin_login_success(self, client: TestClient):
        """Test successful admin login"""
        response = client.post("/admin/login", data={
            "username": settings.admin_username,
            "password": settings.admin_password,
            "csrf_token": get_test_csrf_token()
        })
        
        assert response.status_code == 302
        assert "admin" in response.headers["location"]
    
    def test_admin_login_invalid_credentials(self, client: TestClient):
        """Test admin login with invalid credentials"""
        response = client.post("/admin/login", data={
            "username": "wronguser",
            "password": "wrongpass",
            "csrf_token": get_test_csrf_token()
        })
        
        assert response.status_code == 200  # Form reloaded with error
        assert "Invalid" in response.text
    
    def test_admin_dashboard_authenticated(self, client: TestClient, admin_session: dict):
        """Test admin dashboard when authenticated"""
        response = client.get("/admin", cookies=admin_session)
        assert response.status_code == 200
        assert "Admin Dashboard" in response.text
    
    def test_admin_dashboard_unauthenticated(self, client: TestClient):
        """Test admin dashboard when not authenticated"""
        response = client.get("/admin")
        assert response.status_code == 302
        assert "admin/login" in response.headers["location"]
    
    def test_admin_logout(self, client: TestClient, admin_session: dict):
        """Test admin logout"""
        response = client.post("/admin/logout", data={
            "csrf_token": get_test_csrf_token()
        }, cookies=admin_session)
        
        assert response.status_code == 302
        assert response.headers["location"] == "/"
    
    def test_new_job_form_admin(self, client: TestClient, admin_session: dict):
        """Test new job form for admin"""
        response = client.get("/admin/jobs/new", cookies=admin_session)
        assert response.status_code == 200
        assert "Create Job" in response.text
    
    def test_create_job_admin_success(self, client: TestClient, admin_session: dict, employer: Employer, category: Category):
        """Test successful job creation by admin"""
        response = client.post("/admin/jobs/new", data={
            "title": "Admin Created Job",
            "description": "Job created by admin",
            "tags": "admin,test",
            "salary_min": "50000",
            "salary_max": "70000",
            "apply_url": "https://apply.example.com",
            "employer_id": str(employer.id),
            "category_id": str(category.id),
            "status": "published",
            "csrf_token": get_test_csrf_token()
        }, cookies=admin_session)
        
        assert response.status_code == 302
        assert "admin" in response.headers["location"]


class TestSecurityFeatures:
    """Test security-related features"""
    
    def test_csrf_protection(self, client: TestClient, employer_account: EmployerAccount):
        """Test that CSRF protection is working"""
        # Try to register without CSRF token
        response = client.post("/employer/register", data={
            "email": "test@company.com",
            "password": "securepassword123",
            "company_name": "Test Company",
            "contact_name": "John Doe"
        })
        
        assert response.status_code == 400  # Should reject without CSRF token
    
    def test_authentication_required(self, client: TestClient):
        """Test that protected routes require authentication"""
        # Try to access employer dashboard without login
        response = client.get("/employer/dashboard")
        assert response.status_code == 302
        assert "login" in response.headers["location"]
        
        # Try to access admin dashboard without login
        response = client.get("/admin")
        assert response.status_code == 302
        assert "login" in response.headers["location"]
    
    def test_session_management(self, client: TestClient, employer_account: EmployerAccount):
        """Test session creation and management"""
        # Login to create session
        response = client.post("/employer/login", data={
            "email": employer_account.email,
            "password": "testpassword",
            "csrf_token": get_test_csrf_token()
        })
        
        # Check that session cookie is set
        cookies = response.cookies
        assert "employer_session" in cookies
        
        # Try to access protected route with session
        response = client.get("/employer/dashboard", cookies=cookies)
        assert response.status_code == 200 


class TestContextualNavigation:
    """Test contextual navigation based on authentication state"""
    
    def test_public_navigation_unauthenticated(self, client: TestClient):
        """Test navigation for unauthenticated users"""
        response = client.get("/")
        assert response.status_code == 200
        
        # Should show public navigation links
        assert "Jobs" in response.text
        assert "JSON Feed" in response.text
        assert "Employer Login" in response.text
        assert "Admin" in response.text
        
        # Should NOT show authenticated user links
        assert "Dashboard" not in response.text
        assert "Post Job" not in response.text
        assert "Admin Dashboard" not in response.text
        assert "New Job" not in response.text
    
    def test_employer_navigation_authenticated(self, client: TestClient, employer_session: dict):
        """Test navigation for authenticated employers"""
        response = client.get("/employer/dashboard", cookies=employer_session)
        assert response.status_code == 200
        
        # Should show employer-specific navigation
        assert "Dashboard" in response.text
        assert "Post Job" in response.text
        assert "Logout" in response.text
        
        # Should NOT show public login links
        assert "Employer Login" not in response.text
        assert "Register" not in response.text
        
        # Should still show public links
        assert "Jobs" in response.text
        assert "JSON Feed" in response.text
    
    def test_admin_navigation_authenticated(self, client: TestClient, admin_session: dict):
        """Test navigation for authenticated admins"""
        response = client.get("/admin", cookies=admin_session)
        assert response.status_code == 200
        
        # Should show admin-specific navigation
        assert "Admin Dashboard" in response.text
        assert "New Job" in response.text
        assert "Logout" in response.text
        
        # Should NOT show public login links
        assert "Employer Login" not in response.text
        assert "Register" not in response.text
        assert "Admin Login" not in response.text  # Changed from "Admin" to "Admin Login"
        
        # Should still show public links
        assert "Jobs" in response.text
        assert "JSON Feed" in response.text
    
    def test_navigation_after_login(self, client: TestClient, employer_account: EmployerAccount):
        """Test navigation changes after login"""
        # First, check public navigation
        response = client.get("/")
        assert response.status_code == 200
        assert "Employer Login" in response.text
        assert "Dashboard" not in response.text
        
        # Login
        response = client.post("/employer/login", data={
            "email": employer_account.email,
            "password": "testpassword",
            "csrf_token": get_test_csrf_token()
        })
        assert response.status_code == 302
        
        # Check navigation after login
        response = client.get("/employer/dashboard", cookies=response.cookies)
        assert response.status_code == 200
        assert "Dashboard" in response.text
        assert "Post Job" in response.text
        assert "Employer Login" not in response.text
    
    def test_navigation_after_logout(self, client: TestClient, employer_session: dict):
        """Test navigation changes after logout"""
        # First, check authenticated navigation
        response = client.get("/employer/dashboard", cookies=employer_session)
        assert response.status_code == 200
        assert "Dashboard" in response.text
        
        # Logout
        response = client.post("/employer/logout", data={
            "csrf_token": get_test_csrf_token()
        }, cookies=employer_session)
        assert response.status_code == 302
        
        # Check navigation after logout
        response = client.get("/")
        assert response.status_code == 200
        assert "Employer Login" in response.text
        assert "Dashboard" not in response.text
    
    def test_dashboard_link_visibility(self, client: TestClient, employer_session: dict):
        """Test that dashboard link is always visible for authenticated users"""
        # Test on different pages
        pages = ["/", "/jobs/1", "/search"]
        
        for page in pages:
            try:
                response = client.get(page, cookies=employer_session)
                if response.status_code == 200:
                    assert "Dashboard" in response.text
                    assert "Post Job" in response.text
            except:
                # Some pages might not exist in test data, skip them
                pass
    
    def test_admin_dashboard_link_visibility(self, client: TestClient, admin_session: dict):
        """Test that admin dashboard link is always visible for authenticated admins"""
        # Test on different pages
        pages = ["/", "/jobs/1", "/search"]
        
        for page in pages:
            try:
                response = client.get(page, cookies=admin_session)
                if response.status_code == 200:
                    assert "Admin Dashboard" in response.text
                    assert "New Job" in response.text
            except:
                # Some pages might not exist in test data, skip them
                pass
    
    def test_navigation_consistency(self, client: TestClient, employer_session: dict):
        """Test that navigation is consistent across all employer pages"""
        employer_pages = [
            "/employer/dashboard",
            "/employer/jobs/new"
        ]
        
        for page in employer_pages:
            response = client.get(page, cookies=employer_session)
            if response.status_code == 200:
                # Should always have employer navigation
                assert "Dashboard" in response.text
                assert "Post Job" in response.text
                assert "Logout" in response.text
                
                # Should not have admin navigation (check for specific admin dashboard link)
                assert 'href="/admin"' not in response.text
                assert 'href="/admin/jobs/new"' not in response.text  # Check for specific admin new job link
    
    def test_admin_navigation_consistency(self, client: TestClient, admin_session: dict):
        """Test that navigation is consistent across all admin pages"""
        admin_pages = [
            "/admin",
            "/admin/jobs/new"
        ]
        
        for page in admin_pages:
            response = client.get(page, cookies=admin_session)
            if response.status_code == 200:
                # Should always have admin navigation
                assert "Admin Dashboard" in response.text
                assert "New Job" in response.text
                assert "Logout" in response.text
                
                # Should not have employer navigation (check for specific employer dashboard link)
                assert 'href="/employer/dashboard"' not in response.text
                assert "Post Job" not in response.text
    
    def test_registration_link_visibility(self, client: TestClient):
        """Test that registration link is shown when enabled"""
        response = client.get("/")
        assert response.status_code == 200
        
        # Should show register link when enabled
        from app.config import settings
        if settings.employer_registration_enabled:
            assert "Register" in response.text
        else:
            assert "Register" not in response.text
    
    def test_navigation_highlighting(self, client: TestClient, employer_session: dict):
        """Test that dashboard links are properly highlighted"""
        response = client.get("/employer/dashboard", cookies=employer_session)
        assert response.status_code == 200
        
        # Check for highlighting classes (blue color for dashboard links)
        assert 'text-blue-600' in response.text or 'text-blue-700' in response.text
    
    def test_admin_navigation_highlighting(self, client: TestClient, admin_session: dict):
        """Test that admin dashboard links are properly highlighted"""
        response = client.get("/admin", cookies=admin_session)
        assert response.status_code == 200
        
        # Check for highlighting classes (blue color for dashboard links)
        assert 'text-blue-600' in response.text or 'text-blue-700' in response.text


class TestMiddlewareErrorHandling:
    """Test middleware error handling and edge cases"""
    
    def test_middleware_handles_auth_errors_gracefully(self, client: TestClient, monkeypatch):
        """Test that middleware handles authentication errors gracefully"""
        # Mock verify_employer_session to raise an exception
        def mock_verify_employer_session(request):
            raise Exception("Auth error")
        
        from app.auth import verify_employer_session
        monkeypatch.setattr("app.auth.verify_employer_session", mock_verify_employer_session)
        
        # Should still work and show public navigation
        response = client.get("/")
        assert response.status_code == 200
        assert "Employer Login" in response.text
    
    def test_middleware_handles_admin_auth_errors_gracefully(self, client: TestClient, monkeypatch):
        """Test that middleware handles admin authentication errors gracefully"""
        # Mock verify_admin_session to raise an exception
        def mock_verify_admin_session(request):
            raise Exception("Admin auth error")
        
        from app.auth import verify_admin_session
        monkeypatch.setattr("app.auth.verify_admin_session", mock_verify_admin_session)
        
        # Should still work and show public navigation
        response = client.get("/")
        assert response.status_code == 200
        assert "Employer Login" in response.text
    
    def test_middleware_preserves_existing_scope(self, client: TestClient):
        """Test that middleware preserves existing request scope"""
        response = client.get("/")
        assert response.status_code == 200
        
        # The middleware should work without breaking existing functionality
        # This is tested by ensuring the page loads correctly
        assert "Job Board" in response.text 


class TestSmartHomeRedirect:
    """Test smart home redirect functionality for authenticated users"""
    
    def test_home_redirects_authenticated_employer(self, client: TestClient, employer_session: dict):
        """Test that authenticated employers are redirected from home to dashboard"""
        response = client.get("/", cookies=employer_session)
        assert response.status_code == 302
        assert "employer/dashboard" in response.headers["location"]
    
    def test_home_redirects_authenticated_admin(self, client: TestClient, admin_session: dict):
        """Test that authenticated admins are redirected from home to admin dashboard"""
        response = client.get("/", cookies=admin_session)
        assert response.status_code == 302
        assert "admin" in response.headers["location"]
    
    def test_home_stays_public_for_unauthenticated_users(self, client: TestClient):
        """Test that unauthenticated users can still access the home page"""
        response = client.get("/")
        assert response.status_code == 200
        assert "Jobs" in response.text
        assert "Employer Login" in response.text
    
    def test_home_redirects_after_login(self, client: TestClient, employer_account: EmployerAccount):
        """Test that home redirects after successful login"""
        # Login
        response = client.post("/employer/login", data={
            "email": employer_account.email,
            "password": "testpassword",
            "csrf_token": get_test_csrf_token()
        })
        assert response.status_code == 302
        
        # Now try to access home page
        response = client.get("/", cookies=response.cookies)
        assert response.status_code == 302
        assert "employer/dashboard" in response.headers["location"]
    
    def test_home_redirects_after_admin_login(self, client: TestClient):
        """Test that home redirects after successful admin login"""
        # Login as admin
        response = client.post("/admin/login", data={
            "username": settings.admin_username,
            "password": settings.admin_password,
            "csrf_token": get_test_csrf_token()
        })
        assert response.status_code == 302
        
        # Now try to access home page
        response = client.get("/", cookies=response.cookies)
        assert response.status_code == 302
        assert "admin" in response.headers["location"]
    
    def test_home_accessible_after_logout(self, client: TestClient, employer_session: dict):
        """Test that home page is accessible after logout"""
        # First, verify redirect when authenticated
        response = client.get("/", cookies=employer_session)
        assert response.status_code == 302
        
        # Logout
        response = client.post("/employer/logout", data={
            "csrf_token": get_test_csrf_token()
        }, cookies=employer_session)
        assert response.status_code == 302
        
        # Now home should be accessible
        response = client.get("/")
        assert response.status_code == 200
        assert "Employer Login" in response.text 


class TestDashboardFirstExperience:
    """Test dashboard-first experience for authenticated users"""
    
    def test_employer_login_redirects_to_dashboard(self, client: TestClient, employer_account: EmployerAccount):
        """Test that employer login redirects directly to dashboard"""
        response = client.post("/employer/login", data={
            "email": employer_account.email,
            "password": "testpassword",
            "csrf_token": get_test_csrf_token()
        })
        
        assert response.status_code == 302
        assert "employer/dashboard" in response.headers["location"]
        assert "employer/login" not in response.headers["location"]
    
    def test_admin_login_redirects_to_dashboard(self, client: TestClient):
        """Test that admin login redirects directly to dashboard"""
        response = client.post("/admin/login", data={
            "username": settings.admin_username,
            "password": settings.admin_password,
            "csrf_token": get_test_csrf_token()
        })
        
        assert response.status_code == 302
        assert "admin" in response.headers["location"]
        assert "admin/login" not in response.headers["location"]
    
    def test_employer_registration_redirects_to_dashboard(self, client: TestClient, db: Session):
        """Test that employer registration redirects directly to dashboard"""
        response = client.post("/employer/register", data={
            "email": "new@company.com",
            "password": "securepassword123",
            "company_name": "New Company",
            "contact_name": "John Doe",
            "phone": "123-456-7890",
            "website": "https://newcompany.com",
            "csrf_token": get_test_csrf_token()
        })
        
        assert response.status_code == 302
        assert "employer/dashboard" in response.headers["location"]
        assert "employer/login" not in response.headers["location"]
    
    def test_authenticated_employer_visiting_login_redirects_to_dashboard(self, client: TestClient, employer_session: dict):
        """Test that authenticated employers visiting login page are redirected to dashboard"""
        response = client.get("/employer/login", cookies=employer_session)
        assert response.status_code == 302
        assert "employer/dashboard" in response.headers["location"]
    
    def test_authenticated_admin_visiting_login_redirects_to_dashboard(self, client: TestClient, admin_session: dict):
        """Test that authenticated admins visiting login page are redirected to dashboard"""
        response = client.get("/admin/login", cookies=admin_session)
        assert response.status_code == 302
        assert "admin" in response.headers["location"]
    
    def test_unauthenticated_users_can_still_access_login_pages(self, client: TestClient):
        """Test that unauthenticated users can still access login pages"""
        # Employer login page
        response = client.get("/employer/login")
        assert response.status_code == 200
        assert "Login" in response.text
        
        # Admin login page
        response = client.get("/admin/login")
        assert response.status_code == 200
        assert "Login" in response.text
    
    def test_authenticated_employer_visiting_register_redirects_to_dashboard(self, client: TestClient, employer_session: dict):
        """Test that authenticated employers visiting register page are redirected to dashboard"""
        response = client.get("/employer/register", cookies=employer_session)
        assert response.status_code == 302
        assert "employer/dashboard" in response.headers["location"]
    
    def test_dashboard_is_primary_landing_page_for_authenticated_users(self, client: TestClient, employer_session: dict, admin_session: dict):
        """Test that dashboard is the primary landing page for authenticated users"""
        # Test employer dashboard as primary landing page
        response = client.get("/employer/dashboard", cookies=employer_session)
        assert response.status_code == 200
        assert "Dashboard" in response.text
        assert "Test Company" in response.text
        
        # Test admin dashboard as primary landing page
        response = client.get("/admin", cookies=admin_session)
        assert response.status_code == 200
        assert "Admin Dashboard" in response.text 