#!/usr/bin/env python
"""
Test runner script for the MCP Browser Automation project.
Provides convenient commands for running different test suites.
"""
import subprocess
import sys
import argparse
from pathlib import Path


def run_command(cmd):
    """Run a command and return the exit code."""
    print(f"Running: {' '.join(cmd)}")
    print("-" * 60)
    return subprocess.call(cmd)


def main():
    parser = argparse.ArgumentParser(description="Run tests for MCP Browser Automation")
    parser.add_argument(
        "suite",
        nargs="?",
        default="unit",
        choices=["all", "unit", "integration", "e2e", "performance", "coverage"],
        help="Test suite to run (default: unit)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "-k",
        dest="keyword",
        help="Run tests matching the given keyword expression"
    )
    parser.add_argument(
        "-x",
        dest="exitfirst",
        action="store_true",
        help="Exit on first failure"
    )
    parser.add_argument(
        "--lf",
        dest="last_failed",
        action="store_true",
        help="Run only tests that failed last time"
    )
    
    args = parser.parse_args()
    
    # Base pytest command
    cmd = ["pytest"]
    
    # Add verbosity
    if args.verbose:
        cmd.append("-vv")
    
    # Add exit on first failure
    if args.exitfirst:
        cmd.append("-x")
    
    # Add last failed
    if args.last_failed:
        cmd.append("--lf")
    
    # Add keyword filter
    if args.keyword:
        cmd.extend(["-k", args.keyword])
    
    # Suite-specific options
    if args.suite == "all":
        # Run all tests
        print("Running all tests...")
    elif args.suite == "unit":
        # Run only unit tests (exclude integration, e2e)
        print("Running unit tests...")
        cmd.extend(["-m", "not integration and not e2e and not performance"])
    elif args.suite == "integration":
        # Run integration tests
        print("Running integration tests...")
        cmd.extend(["-m", "integration"])
    elif args.suite == "e2e":
        # Run end-to-end tests
        print("Running end-to-end tests...")
        cmd.extend(["-m", "e2e"])
    elif args.suite == "performance":
        # Run performance tests
        print("Running performance tests...")
        cmd.extend(["-m", "performance"])
    elif args.suite == "coverage":
        # Run with coverage
        print("Running tests with coverage...")
        cmd.extend([
            "--cov=src",
            "--cov-report=html",
            "--cov-report=term-missing",
            "-m", "not e2e"  # Exclude E2E from coverage
        ])
    
    # Run the command
    exit_code = run_command(cmd)
    
    if args.suite == "coverage" and exit_code == 0:
        print("\nCoverage report generated in htmlcov/index.html")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()