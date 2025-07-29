from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./job_board.db"
    
    # Admin Authentication
    admin_username: str = "admin"
    admin_password: str = "changeme"
    secret_key: str = "your-secret-key-change-in-production"
    
    # Stripe Configuration
    stripe_secret_key: str = "sk_test_placeholder"
    stripe_publishable_key: str = "pk_test_placeholder"
    stripe_webhook_secret: str = "whsec_placeholder"
    stripe_price_id: str = "price_placeholder"
    
    # Application Settings
    job_post_price: int = 1000  # $10.00 in cents
    salary_range_required: bool = True
    job_expiry_days: int = 30
    
    # Security
    csrf_secret: str = "csrf-secret-key-change-in-production"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings() 