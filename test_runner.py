# /// script
# dependencies = [
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
Simple test runner using uv's inline script metadata.
Run with: uv run test_runner.py
"""

import subprocess
import sys


def run_tests():
    """Run all tests with coverage"""
    print("🧪 Running Job Board Tests with uv...")
    print("=" * 50)
    
    cmd = [
        "python", "-m", "pytest",
        "--cov=app",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--tb=short",
        "-v"
    ]
    
    try:
        result = subprocess.run(cmd, check=False)
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


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1) 