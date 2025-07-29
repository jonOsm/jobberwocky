#!/usr/bin/env python3
"""
Seed script to populate the database with sample data for testing.
Run with: python scripts/seed_data.py
"""

import sys
import os
from datetime import datetime, timedelta, timezone

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app.models import Base, Job, Employer, Category
from app.config import settings

def create_sample_data():
    """Create sample employers, categories, and jobs"""
    db = SessionLocal()
    
    try:
        # Create employers
        employers = [
            Employer(
                name="TechCorp Inc.",
                website="https://techcorp.com",
                description="A leading technology company focused on innovative solutions."
            ),
            Employer(
                name="StartupXYZ",
                website="https://startupxyz.com",
                description="A fast-growing startup in the mobile development space."
            ),
            Employer(
                name="RemoteWorks",
                website="https://remoteworks.com",
                description="A remote-first company building the future of work."
            ),
            Employer(
                name="DataFlow Systems",
                website="https://dataflow.com",
                description="Specializing in data analytics and machine learning solutions."
            )
        ]
        
        for employer in employers:
            db.add(employer)
        db.commit()
        
        # Create categories
        categories = [
            Category(
                name="Software Development",
                slug="software-development",
                description="Full-stack, frontend, and backend development roles."
            ),
            Category(
                name="Mobile Development",
                slug="mobile-development",
                description="iOS, Android, and cross-platform mobile development."
            ),
            Category(
                name="Data Science",
                slug="data-science",
                description="Machine learning, analytics, and data engineering roles."
            ),
            Category(
                name="DevOps & Infrastructure",
                slug="devops-infrastructure",
                description="Cloud infrastructure, CI/CD, and system administration."
            ),
            Category(
                name="Product Management",
                slug="product-management",
                description="Product strategy, roadmap, and feature development."
            )
        ]
        
        for category in categories:
            db.add(category)
        db.commit()
        
        # Create sample jobs
        jobs = [
            Job(
                title="Senior Flutter Developer",
                description="""
# Senior Flutter Developer

We're looking for an experienced Flutter developer to join our mobile team.

## Responsibilities:
- Develop high-quality mobile applications using Flutter
- Collaborate with design and product teams
- Write clean, maintainable code
- Participate in code reviews and technical discussions

## Requirements:
- 3+ years of experience with Flutter/Dart
- Strong understanding of mobile app architecture
- Experience with state management (Provider, Bloc, Riverpod)
- Knowledge of REST APIs and JSON
- Experience with Git and version control

## Benefits:
- Competitive salary
- Remote work options
- Health insurance
- Professional development budget
                """.strip(),
                tags="flutter, mobile, dart, remote",
                salary_min=90000,
                salary_max=120000,
                salary_currency="USD",
                apply_url="https://techcorp.com/careers/flutter-developer",
                employer_id=employers[0].id,
                category_id=categories[1].id,
                status="published",
                published_at=datetime.now(timezone.utc) - timedelta(days=5),
                expires_at=datetime.now(timezone.utc) + timedelta(days=25)
            ),
            Job(
                title="Python Backend Developer",
                description="""
# Python Backend Developer

Join our backend team to build scalable APIs and services.

## Responsibilities:
- Design and implement RESTful APIs
- Work with databases (PostgreSQL, Redis)
- Write unit and integration tests
- Deploy and maintain services in production

## Requirements:
- 2+ years of Python experience
- Experience with FastAPI or Django
- Knowledge of SQL and database design
- Understanding of microservices architecture
- Experience with Docker and Kubernetes

## Benefits:
- Competitive salary
- Flexible working hours
- Learning and development opportunities
                """.strip(),
                tags="python, backend, fastapi, postgresql",
                salary_min=80000,
                salary_max=110000,
                salary_currency="USD",
                apply_url="https://startupxyz.com/careers/python-developer",
                employer_id=employers[1].id,
                category_id=categories[0].id,
                status="published",
                published_at=datetime.now(timezone.utc) - timedelta(days=3),
                expires_at=datetime.now(timezone.utc) + timedelta(days=27)
            ),
            Job(
                title="Data Scientist",
                description="""
# Data Scientist

Help us extract insights from data and build machine learning models.

## Responsibilities:
- Analyze large datasets to identify patterns
- Build and deploy machine learning models
- Create data visualizations and reports
- Collaborate with product teams on data-driven decisions

## Requirements:
- MS/PhD in Computer Science, Statistics, or related field
- Experience with Python (pandas, numpy, scikit-learn)
- Knowledge of SQL and data warehousing
- Experience with deep learning frameworks (TensorFlow, PyTorch)
- Strong statistical analysis skills

## Benefits:
- Competitive salary
- Remote work available
- Conference attendance
- Latest hardware and tools
                """.strip(),
                tags="python, machine-learning, data-science, remote",
                salary_min=100000,
                salary_max=140000,
                salary_currency="USD",
                apply_url="https://dataflow.com/careers/data-scientist",
                employer_id=employers[3].id,
                category_id=categories[2].id,
                status="published",
                published_at=datetime.now(timezone.utc) - timedelta(days=1),
                expires_at=datetime.now(timezone.utc) + timedelta(days=29)
            ),
            Job(
                title="DevOps Engineer",
                description="""
# DevOps Engineer

Build and maintain our cloud infrastructure and deployment pipelines.

## Responsibilities:
- Manage AWS/GCP cloud infrastructure
- Implement CI/CD pipelines
- Monitor system performance and reliability
- Automate deployment and configuration management

## Requirements:
- 3+ years of DevOps experience
- Experience with AWS, Docker, Kubernetes
- Knowledge of Terraform or CloudFormation
- Experience with monitoring tools (Prometheus, Grafana)
- Strong scripting skills (Bash, Python)

## Benefits:
- Competitive salary
- Remote work options
- Professional certifications
- Modern tech stack
                """.strip(),
                tags="devops, aws, docker, kubernetes",
                salary_min=95000,
                salary_max=130000,
                salary_currency="USD",
                apply_url="https://remoteworks.com/careers/devops-engineer",
                employer_id=employers[2].id,
                category_id=categories[3].id,
                status="draft"
            ),
            Job(
                title="Product Manager",
                description="""
# Product Manager

Lead product strategy and development for our mobile applications.

## Responsibilities:
- Define product vision and roadmap
- Gather and prioritize user requirements
- Work with engineering and design teams
- Analyze user feedback and metrics

## Requirements:
- 3+ years of product management experience
- Experience with mobile app products
- Strong analytical and communication skills
- Experience with agile development methodologies
- Technical background preferred

## Benefits:
- Competitive salary
- Equity options
- Professional development
- Flexible work environment
                """.strip(),
                tags="product-management, mobile, agile, remote",
                salary_min=85000,
                salary_max=115000,
                salary_currency="USD",
                apply_url="https://techcorp.com/careers/product-manager",
                employer_id=employers[0].id,
                category_id=categories[4].id,
                status="published",
                published_at=datetime.now(timezone.utc) - timedelta(days=10),
                expires_at=datetime.now(timezone.utc) + timedelta(days=20)
            )
        ]
        
        for job in jobs:
            db.add(job)
        db.commit()
        
        print("✅ Sample data created successfully!")
        print(f"📊 Created {len(employers)} employers")
        print(f"📂 Created {len(categories)} categories")
        print(f"💼 Created {len(jobs)} jobs")
        print("\n🔗 Visit http://localhost:8000 to see the job board")
        print("🔐 Admin dashboard: http://localhost:8000/admin (admin/changeme)")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    print("🌱 Seeding database with sample data...")
    create_sample_data() 