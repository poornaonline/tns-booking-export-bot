#!/usr/bin/env python3
"""
Test runner script for TNS Booking Uploader Bot.
"""

import sys
import subprocess
from pathlib import Path

def run_tests():
    """Run all tests with appropriate configuration."""
    
    # Add src to Python path
    src_path = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_path))
    
    # Run pytest with configuration
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--disable-warnings"
    ]
    
    print("Running TNS Booking Uploader Bot tests...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

def run_specific_test(test_file):
    """Run a specific test file."""
    
    # Add src to Python path
    src_path = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_path))
    
    cmd = [
        sys.executable, "-m", "pytest",
        f"tests/{test_file}",
        "-v",
        "--tb=short"
    ]
    
    print(f"Running specific test: {test_file}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except Exception as e:
        print(f"Error running test: {e}")
        return 1

def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Run specific test file
        test_file = sys.argv[1]
        if not test_file.startswith("test_"):
            test_file = f"test_{test_file}"
        if not test_file.endswith(".py"):
            test_file = f"{test_file}.py"
        
        return run_specific_test(test_file)
    else:
        # Run all tests
        return run_tests()

if __name__ == "__main__":
    sys.exit(main())
