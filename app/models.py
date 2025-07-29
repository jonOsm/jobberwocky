from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.database import Base
from app.config import settings


class EmployerAccount(Base):
    __tablename__ = "employer_accounts"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=False)
    contact_name = Column(String(255), nullable=False)
    phone = Column(String(50))
    website = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    employers = relationship("Employer", back_populates="account")
    jobs = relationship("Job", back_populates="employer_account")


class Employer(Base):
    __tablename__ = "employers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    website = Column(String(255))
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Link to employer account
    account_id = Column(Integer, ForeignKey("employer_accounts.id"))
    account = relationship("EmployerAccount", back_populates="employers")
    
    jobs = relationship("Job", back_populates="employer")


class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
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
    
    # Link to employer account
    employer_account_id = Column(Integer, ForeignKey("employer_accounts.id"))
    employer_account = relationship("EmployerAccount", back_populates="jobs")
    
    category_id = Column(Integer, ForeignKey("categories.id"))
    category = relationship("Category", back_populates="jobs")
    
    # Status and timestamps
    status = Column(String(20), default="draft")  # draft, published, expired, refunded
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    published_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    
    # Stripe payment info
    stripe_payment_intent_id = Column(String(255))
    payment_completed = Column(Boolean, default=False)
    payment_amount = Column(Integer)  # Amount in cents
    
    # Refund tracking
    refund_requested_at = Column(DateTime(timezone=True))
    refund_processed_at = Column(DateTime(timezone=True))
    refund_reason = Column(Text)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.status == "published" and not self.published_at:
            self.published_at = datetime.now(timezone.utc)
        if self.status == "published" and not self.expires_at:
            self.expires_at = datetime.now(timezone.utc) + timedelta(days=settings.job_expiry_days)
    
    @property
    def is_expired(self) -> bool:
        if self.expires_at:
            # Handle both timezone-aware and timezone-naive datetimes
            expires_at = self.expires_at
            if expires_at and expires_at.tzinfo is None:
                # If naive, assume UTC
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            return datetime.now(timezone.utc) > expires_at
        return False
    
    @property
    def can_refund(self) -> bool:
        """Check if job is within refund window"""
        if not self.published_at or self.status != "published":
            return False
        
        # Handle both timezone-aware and timezone-naive datetimes
        published_at = self.published_at
        if published_at and published_at.tzinfo is None:
            # If naive, assume UTC
            published_at = published_at.replace(tzinfo=timezone.utc)
        
        refund_deadline = published_at + timedelta(hours=settings.refund_window_hours)
        return datetime.now(timezone.utc) <= refund_deadline
    
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
            "can_refund": self.can_refund,
        } 