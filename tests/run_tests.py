#!/usr/bin/env python3
"""
Simple test runner for the job board application.
Run this script to execute all tests with coverage reporting.
"""

import subprocess
import sys
import os


def run_tests():
    """Run all tests with coverage"""
    print("🧪 Running Job Board Tests...")
    print("=" * 50)
    
    # Run pytest with coverage
    cmd = [
        "uv", "run", "pytest",
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
    """Run only unit tests"""
    print("🧪 Running Unit Tests...")
    print("=" * 30)
    
    cmd = [
        "uv", "run", "pytest",
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
    """Run only integration tests"""
    print("🧪 Running Integration Tests...")
    print("=" * 35)
    
    cmd = [
        "uv", "run", "pytest",
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
    """Run tests quickly without coverage"""
    print("🧪 Running Quick Tests...")
    print("=" * 25)
    
    cmd = [
        "uv", "run", "pytest",
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