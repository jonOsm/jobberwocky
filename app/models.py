from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.database import Base
from app.config import settings


class Employer(Base):
    __tablename__ = "employers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    website = Column(String(255))
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    jobs = relationship("Job", back_populates="employer")


class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    jobs = relationship("Job", back_populates="category")


class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    tags = Column(String(500))  # Comma-separated tags
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    salary_currency = Column(String(3), default="USD")
    apply_url = Column(String(500), nullable=False)
    
    # Relationships
    employer_id = Column(Integer, ForeignKey("employers.id"), nullable=False)
    employer = relationship("Employer", back_populates="jobs")
    
    category_id = Column(Integer, ForeignKey("categories.id"))
    category = relationship("Category", back_populates="jobs")
    
    # Status and timestamps
    status = Column(String(20), default="draft")  # draft, published, expired
    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime)
    expires_at = Column(DateTime)
    
    # Stripe payment info
    stripe_payment_intent_id = Column(String(255))
    payment_completed = Column(Boolean, default=False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.status == "published" and not self.published_at:
            self.published_at = datetime.now(timezone.utc)
        if self.status == "published" and not self.expires_at:
            self.expires_at = datetime.now(timezone.utc) + timedelta(days=settings.job_expiry_days)
    
    @property
    def is_expired(self) -> bool:
        if self.expires_at:
            return datetime.now(timezone.utc) > self.expires_at
        return False
    
    @property
    def tag_list(self) -> list[str]:
        if self.tags:
            return [tag.strip() for tag in self.tags.split(",")]
        return []
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "salary_currency": self.salary_currency,
            "apply_url": self.apply_url,
            "employer_name": self.employer.name if self.employer else None,
            "category_name": self.category.name if self.category else None,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        } 