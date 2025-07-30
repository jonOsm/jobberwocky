from fastapi import FastAPI, Request, Depends, HTTPException, status, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasicCredentials
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from datetime import datetime, timedelta, timezone
import stripe
from typing import List, Optional

from app.database import get_db, engine
from app.models import Base, Job, Employer, Category, EmployerAccount
from app.schemas import JobCreate, JobUpdate, EmployerCreate, CategoryCreate, JobSearchParams, EmployerAccountCreate, EmployerAccountLogin, RefundRequest
from app.auth import security, authenticate_admin, authenticate_admin_plain, generate_csrf_token, verify_csrf_token, create_admin_session, verify_admin_session, clear_admin_session, require_csrf_token, create_employer_session, verify_employer_session, clear_employer_session, get_password_hash, verify_password
from app.config import settings

# Create database tables
Base.metadata.create_all(bind=engine)

# Configure Stripe
stripe.api_key = settings.stripe_secret_key

app = FastAPI(
    title="Job Board",
    description="A minimal, self-hostable job board with Stripe integration",
    version="0.1.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")


@app.middleware("http")
async def add_csrf_token(request: Request, call_next):
    """Add CSRF token and authentication context to request scope"""
    # Add CSRF token to request scope for templates BEFORE processing
    if not hasattr(request, "scope"):
        request.scope = {}
    csrf_token = generate_csrf_token()
    request.scope["csrf_token"] = csrf_token
    print(f"DEBUG: Middleware - Generated CSRF token: {csrf_token}")
    
    # Add settings to request scope
    request.scope["settings"] = settings
    
    # Add authentication context to request scope
    try:
        employer_account_id = verify_employer_session(request)
        request.scope["is_employer"] = bool(employer_account_id)
        request.scope["employer_account_id"] = employer_account_id
    except Exception as e:
        print(f"DEBUG: Middleware - Employer auth error: {e}")
        request.scope["is_employer"] = False
        request.scope["employer_account_id"] = None
    
    try:
        is_admin = verify_admin_session(request)
        request.scope["is_admin"] = is_admin
    except Exception as e:
        print(f"DEBUG: Middleware - Admin auth error: {e}")
        request.scope["is_admin"] = False
    
    response = await call_next(request)
    return response


# Chrome DevTools configuration (optional - stops 404 logs)
@app.get("/.well-known/appspecific/com.chrome.devtools.json")
async def chrome_devtools_config():
    """Return config for Chrome DevTools to stop 404 logs and provide app context"""
    return {
        "version": "1.0",
        "name": "Job Board",
        "description": "FastAPI job board with employer management",
        "framework": "FastAPI",
        "features": ["HTMX", "Stripe", "Employer Accounts"]
    }

# Public routes
@app.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    db: Session = Depends(get_db)
):
    """Home page with job listings and search - redirects authenticated users"""
    # Check for authenticated users and redirect them
    try:
        # Check for employer authentication
        employer_account_id = verify_employer_session(request)
        if employer_account_id:
            return RedirectResponse(url="/employer/dashboard", status_code=302)
    except Exception:
        pass  # Continue to check admin authentication
    
    try:
        # Check for admin authentication
        is_admin = verify_admin_session(request)
        if is_admin:
            return RedirectResponse(url="/admin", status_code=302)
    except Exception:
        pass  # Continue to show public home page
    
    # Get all published jobs for public users
    jobs = db.query(Job).filter(
        Job.status == "published",
        or_(
            Job.expires_at.is_(None),
            Job.expires_at > datetime.now(timezone.utc)
        )
    ).order_by(Job.published_at.desc()).all()
    
    categories = db.query(Category).all()
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "jobs": jobs,
            "categories": categories
        }
    )


@app.get("/search", response_class=HTMLResponse)
async def search_jobs(
    request: Request,
    q: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Search jobs endpoint for HTMX requests"""
    query = db.query(Job).filter(Job.status == "published")
    
    # Search functionality
    if q:
        query = query.filter(
            or_(
                Job.title.ilike(f"%{q}%"),
                Job.tags.ilike(f"%{q}%")
            )
        )
    
    # Category filter
    if category:
        query = query.join(Category).filter(Category.slug == category)
    
    # Tags filter
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
        for tag in tag_list:
            query = query.filter(Job.tags.ilike(f"%{tag}%"))
    
    # Filter out expired jobs
    query = query.filter(
        or_(
            Job.expires_at.is_(None),
            Job.expires_at > datetime.now(timezone.utc)
        )
    )
    
    jobs = query.order_by(Job.published_at.desc()).all()
    
    return templates.TemplateResponse(
        "job_results.html",
        {
            "request": request,
            "jobs": jobs,
            "search_query": q,
            "selected_category": category,
            "selected_tags": tags
        }
    )


@app.get("/jobs/feed.json")
async def jobs_feed(db: Session = Depends(get_db)):
    """JSON feed of published jobs"""
    jobs = db.query(Job).filter(
        Job.status == "published",
        or_(
            Job.expires_at.is_(None),
            Job.expires_at > datetime.now(timezone.utc)
        )
    ).order_by(Job.published_at.desc()).all()
    
    # Return array of jobs directly (standard JSON feed format)
    return [job.to_dict() for job in jobs]


@app.get("/jobs/{job_id}", response_class=HTMLResponse)
async def job_detail(request: Request, job_id: int, db: Session = Depends(get_db)):
    """Job detail page with SEO schema"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return templates.TemplateResponse(
        "job_detail.html",
        {"request": request, "job": job}
    )


@app.get("/sitemap.xml")
async def sitemap(db: Session = Depends(get_db)):
    """XML sitemap for SEO"""
    jobs = db.query(Job).filter(Job.status == "published").all()
    
    sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap_content += '  <url>\n'
    sitemap_content += '    <loc>https://yourdomain.com/</loc>\n'
    sitemap_content += '    <changefreq>daily</changefreq>\n'
    sitemap_content += '  </url>\n'
    
    for job in jobs:
        sitemap_content += '  <url>\n'
        sitemap_content += f'    <loc>https://yourdomain.com/jobs/{job.id}</loc>\n'
        sitemap_content += f'    <lastmod>{job.published_at.isoformat() if job.published_at else job.created_at.isoformat()}</lastmod>\n'
        sitemap_content += '    <changefreq>weekly</changefreq>\n'
        sitemap_content += '  </url>\n'
    
    sitemap_content += '</urlset>'
    
    from fastapi.responses import Response
    return Response(content=sitemap_content, media_type="application/xml")


# Employer routes
@app.get("/employer/register", response_class=HTMLResponse)
async def employer_register_form(request: Request):
    """Employer registration form - redirects authenticated users to dashboard"""
    # Check if registration is enabled
    if not settings.employer_registration_enabled:
        raise HTTPException(status_code=404, detail="Employer registration is disabled")
    
    # Check if user is already authenticated
    try:
        employer_account_id = verify_employer_session(request)
        if employer_account_id:
            return RedirectResponse(url="/employer/dashboard", status_code=302)
    except Exception:
        pass  # Continue to show registration form
    
    return templates.TemplateResponse("employer/register.html", {"request": request})


@app.post("/employer/register")
async def employer_register(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Register a new employer account"""
    print("DEBUG: employer_register called")
    if not settings.employer_registration_enabled:
        raise HTTPException(status_code=404, detail="Employer registration is disabled")

    form_data = await request.form()
    print(f"DEBUG: form_data: {dict(form_data)}")

    # Validate CSRF token
    csrf_token = form_data.get("csrf_token")
    if not csrf_token or not verify_csrf_token(csrf_token):
        raise HTTPException(status_code=400, detail="Invalid CSRF token")

    # Check if email already exists
    existing_account = db.query(EmployerAccount).filter(
        EmployerAccount.email == form_data.get("email")
    ).first()

    if existing_account:
        print("DEBUG: Email already exists")
        return templates.TemplateResponse(
            "employer/register.html",
            {
                "request": request,
                "error": "An account with this email already exists",
                "form_data": dict(form_data)
            }
        )

    # Create employer account
    employer_account = EmployerAccount(
        email=form_data.get("email"),
        password_hash=get_password_hash(form_data.get("password")),
        company_name=form_data.get("company_name"),
        contact_name=form_data.get("contact_name"),
        phone=form_data.get("phone"),
        website=form_data.get("website")
    )

    db.add(employer_account)
    db.commit()
    db.refresh(employer_account)
    print(f"DEBUG: Created employer_account with id: {employer_account.id}")

    # Create associated employer record
    employer = Employer(
        name=employer_account.company_name,
        website=employer_account.website,
        account_id=employer_account.id
    )

    db.add(employer)
    db.commit()
    print(f"DEBUG: Created employer with id: {employer.id}")

    # Create session and redirect to dashboard
    print(f"DEBUG: Creating session for employer_account_id: {employer_account.id}")
    redirect_response = RedirectResponse(url="/employer/dashboard", status_code=302)
    create_employer_session(redirect_response, employer_account.id)
    print("DEBUG: Session created, redirecting to dashboard")
    return redirect_response


@app.get("/employer/login", response_class=HTMLResponse)
async def employer_login_form(request: Request):
    """Employer login form - redirects authenticated users to dashboard"""
    # Check if user is already authenticated
    try:
        employer_account_id = verify_employer_session(request)
        if employer_account_id:
            return RedirectResponse(url="/employer/dashboard", status_code=302)
    except Exception:
        pass  # Continue to show login form
    
    return templates.TemplateResponse("employer/login.html", {"request": request})


@app.post("/employer/login")
async def employer_login(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Employer login"""
    print("DEBUG: employer_login called")
    form_data = await request.form()
    email = form_data.get("email")
    password = form_data.get("password")
    print(f"DEBUG: email: {email}")

    # Find employer account
    employer_account = db.query(EmployerAccount).filter(
        EmployerAccount.email == email,
        EmployerAccount.is_active == True
    ).first()

    if not employer_account:
        print("DEBUG: No employer account found")
        return templates.TemplateResponse(
            "employer/login.html",
            {
                "request": request,
                "error": "Invalid email or password",
                "email": email
            }
        )

    print(f"DEBUG: Found employer account with id: {employer_account.id}")
    
    if not verify_password(password, employer_account.password_hash):
        print("DEBUG: Password verification failed")
        return templates.TemplateResponse(
            "employer/login.html",
            {
                "request": request,
                "error": "Invalid email or password",
                "email": email
            }
        )

    print("DEBUG: Password verified successfully")

    # Update last login
    employer_account.last_login = datetime.now(timezone.utc)
    db.commit()

    # Create session and redirect to dashboard
    print(f"DEBUG: Creating session for employer_account_id: {employer_account.id}")
    redirect_response = RedirectResponse(url="/employer/dashboard", status_code=302)
    create_employer_session(redirect_response, employer_account.id)
    print("DEBUG: Session created, redirecting to dashboard")
    return redirect_response


@app.post("/employer/logout")
async def employer_logout(response: Response):
    """Employer logout"""
    redirect_response = RedirectResponse(url="/", status_code=302)
    clear_employer_session(redirect_response)
    return redirect_response


@app.get("/employer/dashboard", response_class=HTMLResponse)
async def employer_dashboard(
    request: Request,
    db: Session = Depends(get_db)
):
    """Employer dashboard"""
    print("DEBUG: employer_dashboard called")
    employer_account_id = verify_employer_session(request)
    print(f"DEBUG: employer_account_id: {employer_account_id}")
    
    if not employer_account_id:
        print("DEBUG: No valid session, redirecting to login")
        return RedirectResponse(url="/employer/login", status_code=302)

    employer_account = db.query(EmployerAccount).filter(
        EmployerAccount.id == employer_account_id
    ).first()

    if not employer_account:
        print("DEBUG: No employer account found, redirecting to login")
        return RedirectResponse(url="/employer/login", status_code=302)

    print(f"DEBUG: Found employer account: {employer_account.email}")

    # Get employer's jobs
    jobs = db.query(Job).filter(
        Job.employer_account_id == employer_account_id
    ).order_by(Job.created_at.desc()).all()

    print(f"DEBUG: Found {len(jobs)} jobs for employer")

    # Check for payment success message
    payment_success = request.query_params.get("payment") == "success"
    print(f"DEBUG: payment_success = {payment_success}")
    
    return templates.TemplateResponse(
        "employer/dashboard.html",
        {
            "request": request,
            "employer_account": employer_account,
            "jobs": jobs,
            "payment_success": payment_success
        }
    )


@app.get("/employer/jobs/new", response_class=HTMLResponse)
async def employer_new_job_form(
    request: Request,
    db: Session = Depends(get_db)
):
    """New job form for employers"""
    employer_account_id = verify_employer_session(request)
    if not employer_account_id:
        return RedirectResponse(url="/employer/login", status_code=302)
    
    # Check job limit
    if settings.max_jobs_per_employer:
        job_count = db.query(Job).filter(
            Job.employer_account_id == employer_account_id
        ).count()
        
        if job_count >= settings.max_jobs_per_employer:
            return templates.TemplateResponse(
                "employer/error.html",
                {
                    "request": request,
                    "error": f"You have reached the maximum number of jobs ({settings.max_jobs_per_employer})"
                }
            )
    
    categories = db.query(Category).all()
    employers = db.query(Employer).filter(
        Employer.account_id == employer_account_id
    ).all()
    
    return templates.TemplateResponse(
        "employer/new_job.html",
        {
            "request": request,
            "categories": categories,
            "employers": employers,
            "settings": settings
        }
    )


@app.post("/employer/jobs/new")
async def employer_create_job(
    request: Request,
    db: Session = Depends(get_db)
):
    """Create a new job for employer"""
    print("DEBUG: employer_create_job called")
    employer_account_id = verify_employer_session(request)
    if not employer_account_id:
        return RedirectResponse(url="/employer/login", status_code=302)
    
    form_data = await request.form()
    print(f"DEBUG: form_data keys: {list(form_data.keys())}")
    
    # Validate CSRF token
    csrf_token = form_data.get("csrf_token")
    print(f"DEBUG: csrf_token from form: {csrf_token}")
    if not csrf_token or not verify_csrf_token(csrf_token):
        print(f"DEBUG: CSRF validation failed - token: {csrf_token}")
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
    print("DEBUG: CSRF validation passed")
    
    # Validate salary range if required
    if settings.salary_range_required:
        salary_min = form_data.get("salary_min")
        salary_max = form_data.get("salary_max")
        if not salary_min or not salary_max:
            return templates.TemplateResponse(
                "employer/new_job.html",
                {
                    "request": request,
                    "error": "Salary range is required",
                    "form_data": dict(form_data)
                }
            )
    
    # Create job
    job_data = {
        "title": form_data.get("title"),
        "description": form_data.get("description"),
        "tags": form_data.get("tags"),
        "salary_min": int(form_data.get("salary_min")) if form_data.get("salary_min") else None,
        "salary_max": int(form_data.get("salary_max")) if form_data.get("salary_max") else None,
        "apply_url": form_data.get("apply_url"),
        "employer_id": int(form_data.get("employer_id")),
        "category_id": int(form_data.get("category_id")) if form_data.get("category_id") else None,
        "employer_account_id": employer_account_id,
        "payment_amount": settings.job_post_price
    }
    
    job = Job(**job_data)
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Redirect to payment
    return RedirectResponse(url=f"/employer/jobs/{job.id}/payment", status_code=302)


@app.get("/employer/jobs/{job_id}/payment", response_class=HTMLResponse)
async def employer_job_payment(
    request: Request,
    job_id: int,
    db: Session = Depends(get_db)
):
    """Job payment page"""
    employer_account_id = verify_employer_session(request)
    if not employer_account_id:
        return RedirectResponse(url="/employer/login", status_code=302)
    
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.employer_account_id == employer_account_id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status == "published":
        return RedirectResponse(url=f"/employer/jobs/{job.id}", status_code=302)
    
    return templates.TemplateResponse(
        "employer/job_payment.html",
        {
            "request": request,
            "job": job,
            "stripe_publishable_key": settings.stripe_publishable_key,
            "settings": settings
        }
    )


@app.post("/employer/jobs/{job_id}/refund")
async def employer_request_refund(
    request: Request,
    job_id: int,
    db: Session = Depends(get_db)
):
    """Request a refund for a job"""
    employer_account_id = verify_employer_session(request)
    if not employer_account_id:
        return RedirectResponse(url="/employer/login", status_code=302)
    
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.employer_account_id == employer_account_id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if not job.can_refund:
        raise HTTPException(status_code=400, detail="Job is not eligible for refund")
    
    form_data = await request.form()
    reason = form_data.get("reason")
    
    job.refund_requested_at = datetime.now(timezone.utc)
    job.refund_reason = reason
    job.status = "refunded"
    
    db.commit()
    
    # TODO: Process refund through Stripe
    # For now, just mark as refunded
    
    return templates.TemplateResponse(
        "employer/dashboard.html",
        {
            "request": request,
            "employer_account": db.query(EmployerAccount).filter(EmployerAccount.id == employer_account_id).first(),
            "jobs": db.query(Job).filter(Job.employer_account_id == employer_account_id).order_by(Job.created_at.desc()).all(),
            "refund_success": True,
            "refunded_job": job
        }
    )


# Admin routes
@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_form(request: Request):
    """Admin login form - redirects authenticated users to dashboard"""
    # Check if user is already authenticated
    try:
        is_admin = verify_admin_session(request)
        if is_admin:
            return RedirectResponse(url="/admin", status_code=302)
    except Exception:
        pass  # Continue to show login form
    
    print("DEBUG: Login form accessed")
    import sys
    sys.stdout.flush()
    return templates.TemplateResponse("admin/login.html", {"request": request})


@app.post("/admin/login")
async def admin_login(
    request: Request,
    response: Response
):
    """Admin login"""
    form_data = await request.form()
    raw_username = form_data.get("username", "")
    raw_password = form_data.get("password", "")
    username = raw_username.strip()
    password = raw_password.strip()
    
    print(f"DEBUG: Raw form data - username: '{raw_username}', password: '{raw_password}'")
    print(f"DEBUG: After strip - username: '{username}', password: '{password}'")
    print(f"DEBUG: Expected username: {settings.admin_username}, password: {settings.admin_password}")
    
    # Secure authentication check with password hashing
    auth_result = authenticate_admin_plain(username, password)
    print(f"DEBUG: Authentication result: {auth_result}")
    
    if auth_result:
        print("DEBUG: Authentication successful, creating session and redirecting")
        redirect_response = RedirectResponse(url="/admin?login=success", status_code=302)
        create_admin_session(redirect_response)
        # Redirect with success message
        return redirect_response
    else:
        print("DEBUG: Authentication failed, showing error")
        return templates.TemplateResponse(
            "admin/login.html", 
            {
                "request": request,
                "error": "Invalid username or password",
                "username": username
            }
        )


@app.post("/admin/logout")
async def admin_logout(response: Response):
    """Admin logout"""
    redirect_response = RedirectResponse(url="/", status_code=302)
    clear_admin_session(redirect_response)
    return redirect_response


@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    db: Session = Depends(get_db)
):
    """Admin dashboard"""
    print("DEBUG: admin_dashboard called")
    if not verify_admin_session(request):
        print("DEBUG: No valid session, redirecting to login")
        return RedirectResponse(url="/admin/login", status_code=302)
    
    print("DEBUG: Valid session, loading dashboard")
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    employers = db.query(Employer).all()
    categories = db.query(Category).all()
    
    # Check for login success message
    login_success = request.query_params.get("login") == "success"
    print(f"DEBUG: login_success = {login_success}")
    
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "jobs": jobs,
            "employers": employers,
            "categories": categories,
            "login_success": login_success
        }
    )


@app.get("/admin/jobs/new", response_class=HTMLResponse)
async def new_job_form(
    request: Request,
    db: Session = Depends(get_db)
):
    """New job form"""
    print("DEBUG: new_job_form called")
    if not verify_admin_session(request):
        print("DEBUG: No valid session in new_job_form, redirecting to login")
        return RedirectResponse(url="/admin/login", status_code=302)
    
    employers = db.query(Employer).all()
    categories = db.query(Category).all()
    
    return templates.TemplateResponse(
        "admin/new_job.html",
        {
            "request": request,
            "employers": employers,
            "categories": categories
        }
    )


@app.post("/admin/jobs/new")
async def create_job(
    request: Request,
    db: Session = Depends(get_db)
):
    """Create a new job"""
    if not verify_admin_session(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    
    form_data = await request.form()
    
    # Validate CSRF token
    csrf_token = form_data.get("csrf_token")
    if not csrf_token or not verify_csrf_token(csrf_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
    
    job_data = {
        "title": form_data.get("title"),
        "description": form_data.get("description"),
        "tags": form_data.get("tags"),
        "salary_min": int(form_data.get("salary_min")) if form_data.get("salary_min") else None,
        "salary_max": int(form_data.get("salary_max")) if form_data.get("salary_max") else None,
        "apply_url": form_data.get("apply_url"),
        "employer_id": int(form_data.get("employer_id")),
        "category_id": int(form_data.get("category_id")) if form_data.get("category_id") else None,
    }
    
    # Validate salary range if required
    if settings.salary_range_required:
        if not job_data["salary_min"] or not job_data["salary_max"]:
            raise HTTPException(status_code=400, detail="Salary range is required")
    
    job = Job(**job_data)
    db.add(job)
    db.commit()
    db.refresh(job)
    
    return RedirectResponse(url=f"/admin/jobs/{job.id}", status_code=302)


@app.get("/admin/jobs/{job_id}", response_class=HTMLResponse)
async def edit_job_form(
    request: Request,
    job_id: int,
    db: Session = Depends(get_db)
):
    """Edit job form"""
    if not verify_admin_session(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    employers = db.query(Employer).all()
    categories = db.query(Category).all()
    
    return templates.TemplateResponse(
        "admin/edit_job.html",
        {
            "request": request,
            "job": job,
            "employers": employers,
            "categories": categories
        }
    )


@app.patch("/admin/jobs/{job_id}")
async def update_job(
    request: Request,
    job_id: int,
    db: Session = Depends(get_db)
):
    """Update a job"""
    if not verify_admin_session(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    form_data = await request.form()
    
    # Validate CSRF token
    csrf_token = form_data.get("csrf_token")
    if not csrf_token or not verify_csrf_token(csrf_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
    
    # Update fields
    if form_data.get("title"):
        job.title = form_data.get("title")
    if form_data.get("description"):
        job.description = form_data.get("description")
    if form_data.get("tags"):
        job.tags = form_data.get("tags")
    if form_data.get("salary_min"):
        job.salary_min = int(form_data.get("salary_min"))
    if form_data.get("salary_max"):
        job.salary_max = int(form_data.get("salary_max"))
    if form_data.get("apply_url"):
        job.apply_url = form_data.get("apply_url")
    if form_data.get("employer_id"):
        job.employer_id = int(form_data.get("employer_id"))
    if form_data.get("category_id"):
        job.category_id = int(form_data.get("category_id"))
    
    # Handle status changes
    if form_data.get("status") == "expired":
        job.status = "expired"
    elif form_data.get("status") == "published":
        job.status = "published"
        job.published_at = datetime.now(timezone.utc)
        job.expires_at = datetime.now(timezone.utc) + timedelta(days=settings.job_expiry_days)
    
    db.commit()
    
    return {"status": "success", "message": "Job updated successfully"}


# Stripe integration (Mock for development)
@app.post("/stripe/create-checkout-session")
async def create_checkout_session(
    request: Request,
    db: Session = Depends(get_db)
):
    """Create Stripe checkout session (Mock for development)"""
    form_data = await request.form()
    job_id = int(form_data.get("job_id"))
    
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Mock successful payment for development
    print(f"DEBUG: Mock Stripe payment for job {job_id}")
    
    # Update job as if payment was successful
    job.status = "published"
    job.payment_completed = True
    job.published_at = datetime.now(timezone.utc)
    job.expires_at = datetime.now(timezone.utc) + timedelta(days=settings.job_expiry_days)
    job.stripe_payment_intent_id = f"mock_payment_{job_id}_{datetime.now().timestamp()}"
    db.commit()
    
    print(f"DEBUG: Job {job_id} marked as published")
    
    # Return success response
    return {"id": f"mock_session_{job_id}"}


@app.post("/stripe/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhooks"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        job_id = payment_intent.get("metadata", {}).get("job_id")
        
        if job_id:
            job = db.query(Job).filter(Job.id == int(job_id)).first()
            if job:
                job.status = "published"
                job.payment_completed = True
                job.published_at = datetime.now(timezone.utc)
                job.expires_at = datetime.now(timezone.utc) + timedelta(days=settings.job_expiry_days)
                db.commit()
    
    return {"status": "success"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 