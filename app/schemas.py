from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, HttpUrl, validator, Field, EmailStr


class JobBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=10)
    tags: Optional[str] = Field(None, max_length=500)
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    salary_currency: str = Field(default="USD", max_length=3)
    apply_url: HttpUrl
    
    @validator('salary_max')
    def validate_salary_range(cls, v, values):
        if v is not None and 'salary_min' in values and values['salary_min'] is not None:
            if v < values['salary_min']:
                raise ValueError('salary_max must be greater than or equal to salary_min')
        return v


class JobCreate(JobBase):
    employer_id: int
    category_id: Optional[int] = None


class JobUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    tags: Optional[str] = Field(None, max_length=500)
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    salary_currency: Optional[str] = Field(None, max_length=3)
    apply_url: Optional[HttpUrl] = None
    employer_id: Optional[int] = None
    category_id: Optional[int] = None
    status: Optional[str] = Field(None, pattern="^(draft|published|expired|refunded)$")


class JobResponse(JobBase):
    id: int
    employer_name: str
    category_name: Optional[str] = None
    status: str
    created_at: datetime
    published_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_expired: bool
    can_refund: bool
    payment_amount: Optional[int] = None
    
    class Config:
        from_attributes = True


class EmployerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    website: Optional[HttpUrl] = None
    description: Optional[str] = None


class EmployerCreate(EmployerBase):
    pass


class EmployerResponse(EmployerBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Employer Account Schemas
class EmployerAccountBase(BaseModel):
    email: EmailStr
    company_name: str = Field(..., min_length=1, max_length=255)
    contact_name: str = Field(..., min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    website: Optional[HttpUrl] = None


class EmployerAccountCreate(EmployerAccountBase):
    password: str = Field(..., min_length=8)


class EmployerAccountLogin(BaseModel):
    email: EmailStr
    password: str


class EmployerAccountResponse(EmployerAccountBase):
    id: int
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class EmployerAccountUpdate(BaseModel):
    company_name: Optional[str] = Field(None, min_length=1, max_length=255)
    contact_name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    website: Optional[HttpUrl] = None
    password: Optional[str] = Field(None, min_length=8)


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class JobSearchParams(BaseModel):
    q: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    employer: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(draft|published|expired|refunded)$")


class StripeCheckoutRequest(BaseModel):
    job_id: int
    success_url: HttpUrl
    cancel_url: HttpUrl


class RefundRequest(BaseModel):
    job_id: int
    reason: str = Field(..., min_length=10, max_length=1000) 