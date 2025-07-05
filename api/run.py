#!/usr/bin/env python3
"""
Simple script to run the Newsfax API using uv.
"""
import os
import sys
import subprocess


def run_api():
    """Run the API server."""
    print("Starting Newsfax API server...")
    os.execvp("python", ["python", "hello.py"])


def run_tests():
    """Run the test suite."""
    print("Running tests...")
    result = subprocess.run(["python", "-m", "pytest", "test_factcheck.py", "-v"])
    sys.exit(result.returncode)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        run_tests()
    else:
        run_api()
