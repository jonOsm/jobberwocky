# /// script
# dependencies = [
#   "fastapi>=0.104.0",
#   "uvicorn[standard]>=0.24.0",
#   "jinja2>=3.1.0",
#   "python-multipart>=0.0.6",
#   "sqlalchemy>=2.0.0",
#   "alembic>=1.12.0",
#   "stripe>=7.0.0",
#   "python-dotenv>=1.0.0",
#   "pydantic>=2.0.0",
#   "pydantic-settings>=2.0.0",
#   "httpx>=0.25.0",
#   "python-jose[cryptography]>=3.3.0",
#   "passlib[bcrypt]>=1.7.4",
#   "itsdangerous>=2.1.0",
#   "email-validator>=2.0.0",
#   "pytest>=7.4.0",
#   "pytest-asyncio>=0.21.0", 
#   "pytest-cov>=4.1.0",
#   "pytest-mock>=3.11.0",
#   "factory-boy>=3.3.0",
#   "faker>=19.0.0",
# ]
# ///

#!/usr/bin/env python3
"""
Simple test runner for the job board application.
Run this script to execute all tests with coverage reporting.
Uses uv for dependency management.
"""

import subprocess
import sys
import os


def run_tests():
    """Run all tests with coverage using uv"""
    print("🧪 Running Job Board Tests with uv...")
    print("=" * 50)
    
    # Run pytest with coverage using uv
    cmd = [
        "uv", "run", "python", "-m", "pytest",
        "--cov=app",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--tb=short",
        "-v"
    ]
    
    try:
        result = subprocess.run(cmd, check=False)  # Don't raise exception on failure
        if result.returncode == 0:
            print("\n✅ All tests passed!")
            print(f"📊 Coverage report generated in htmlcov/index.html")
            return True
        else:
            print(f"\n❌ Tests failed with exit code {result.returncode}")
            return False
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        return False


def run_unit_tests():
    """Run only unit tests using uv"""
    print("🧪 Running Unit Tests with uv...")
    print("=" * 30)
    
    cmd = [
        "uv", "run", "python", "-m", "pytest",
        "tests/unit/",
        "-v",
        "--tb=short"
    ]
    
    try:
        result = subprocess.run(cmd, check=False)
        if result.returncode == 0:
            print("\n✅ Unit tests passed!")
            return True
        else:
            print(f"\n❌ Unit tests failed with exit code {result.returncode}")
            return False
    except Exception as e:
        print(f"\n❌ Error running unit tests: {e}")
        return False


def run_integration_tests():
    """Run only integration tests using uv"""
    print("🧪 Running Integration Tests with uv...")
    print("=" * 35)
    
    cmd = [
        "uv", "run", "python", "-m", "pytest",
        "tests/integration/",
        "-v",
        "--tb=short"
    ]
    
    try:
        result = subprocess.run(cmd, check=False)
        if result.returncode == 0:
            print("\n✅ Integration tests passed!")
            return True
        else:
            print(f"\n❌ Integration tests failed with exit code {result.returncode}")
            return False
    except Exception as e:
        print(f"\n❌ Error running integration tests: {e}")
        return False


def run_quick_tests():
    """Run tests quickly without coverage using uv"""
    print("🧪 Running Quick Tests with uv...")
    print("=" * 25)
    
    cmd = [
        "uv", "run", "python", "-m", "pytest",
        "--tb=short",
        "-v"
    ]
    
    try:
        result = subprocess.run(cmd, check=False)
        if result.returncode == 0:
            print("\n✅ Quick tests passed!")
            return True
        else:
            print(f"\n❌ Quick tests failed with exit code {result.returncode}")
            return False
    except Exception as e:
        print(f"\n❌ Error running quick tests: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "unit":
            success = run_unit_tests()
        elif command == "integration":
            success = run_integration_tests()
        elif command == "quick":
            success = run_quick_tests()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: unit, integration, quick")
            sys.exit(1)
    else:
        # Default: run all tests with coverage
        success = run_tests()
    
    sys.exit(0 if success else 1) 