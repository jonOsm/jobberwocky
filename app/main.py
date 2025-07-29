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
from app.models import Base, Job, Employer, Category
from app.schemas import JobCreate, JobUpdate, EmployerCreate, CategoryCreate, JobSearchParams
from app.auth import security, authenticate_admin, authenticate_admin_plain, generate_csrf_token, verify_csrf_token, create_admin_session, verify_admin_session, clear_admin_session, require_csrf_token
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
    """Add CSRF token to all responses"""
    response = await call_next(request)
    # Add CSRF token to request scope for templates
    if not hasattr(request, "scope"):
        request.scope = {}
    request.scope["csrf_token"] = generate_csrf_token()
    return response


# Public routes
@app.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    db: Session = Depends(get_db)
):
    """Home page with job listings and search"""
    # Get all published jobs
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
    
    return {
        "jobs": [job.to_dict() for job in jobs],
        "last_updated": datetime.now(timezone.utc).isoformat()
    }


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
    
    return sitemap_content


# Admin routes
@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_form(request: Request):
    """Admin login form"""
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
        create_admin_session(response)
        # Redirect with success message
        response.headers["Location"] = "/admin?login=success"
        response.status_code = 302
        return response
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
    clear_admin_session(response)
    return RedirectResponse(url="/admin/login", status_code=302)


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
    if not verify_admin_session(request):
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


# Stripe integration
@app.post("/stripe/create-checkout-session")
async def create_checkout_session(
    request: Request,
    db: Session = Depends(get_db)
):
    """Create Stripe checkout session"""
    form_data = await request.form()
    job_id = int(form_data.get("job_id"))
    
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price": settings.stripe_price_id,
                    "quantity": 1,
                },
            ],
            mode="payment",
            success_url=form_data.get("success_url"),
            cancel_url=form_data.get("cancel_url"),
            metadata={"job_id": job_id},
        )
        
        # Update job with payment intent
        job.stripe_payment_intent_id = checkout_session.payment_intent
        db.commit()
        
        return {"id": checkout_session.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


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