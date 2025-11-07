#!/usr/bin/env python3
"""
Pre-push validation script for Telegram Paid Subscriber Service.

This script runs before git push to ensure code quality:
1. Runs linting with ruff
2. Formats code with black (check only)
3. Runs all tests with pytest
4. Blocks push if any checks fail

Usage:
    This script is automatically run by git pre-push hook.
    Can also be run manually: python scripts/pre_push_check.py
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(message):
    """Print a header message."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message:^80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")


def print_success(message):
    """Print a success message."""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_error(message):
    """Print an error message."""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


def print_warning(message):
    """Print a warning message."""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")


def print_info(message):
    """Print an info message."""
    print(f"{Colors.OKBLUE}ℹ {message}{Colors.ENDC}")


def run_command(cmd, description, allow_failure=False):
    """
    Run a command and return True if successful.
    """
    print_info(f"Running: {description}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            print_success(f"{description} passed")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print_error(f"{description} failed")
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)

            if not allow_failure:
                print_error(f"\nPush blocked due to failed check: {description}")
                sys.exit(1)
            return False

    except FileNotFoundError:
        print_warning(f"Command not found, skipping: {' '.join(cmd)}")
        return False
    except Exception as e:
        print_error(f"Error running {description}: {e}")
        if not allow_failure:
            sys.exit(1)
        return False


def check_dependencies():
    """Check if required tools are installed."""
    print_header("Checking Dependencies")

    dependencies = {
        "python": ["python", "--version"],
        "ruff": ["ruff", "--version"],
        "black": ["black", "--version"],
        "pytest": ["pytest", "--version"],
    }

    missing = []
    for name, cmd in dependencies.items():
        try:
            result = subprocess.run(cmd, capture_output=True, check=False)
            if result.returncode == 0:
                print_success(f"{name} is installed")
            else:
                missing.append(name)
                print_warning(f"{name} is not installed")
        except FileNotFoundError:
            missing.append(name)
            print_warning(f"{name} is not installed")

    if missing:
        print_warning(f"\nMissing dependencies: {', '.join(missing)}")
        print_info("Install them with: pip install -r requirements.txt")
        return False

    return True


def run_linting():
    """Run code linting with ruff."""
    print_header("Running Linting (ruff)")

    # Run ruff linting
    success = run_command(
        ["ruff", "check", "app", "tests", "main.py"],
        "Ruff linting",
        allow_failure=False,
    )

    return success


def run_formatting():
    """Check code formatting with black."""
    print_header("Checking Code Formatting (black)")

    # Run black in check mode
    success = run_command(
        ["black", "--check", "--diff", "app", "tests", "main.py"],
        "Black formatting check",
        allow_failure=False,
    )

    if not success:
        print_info("\nTo fix formatting issues, run: black app tests main.py")

    return success


def run_tests():
    """Run all tests with pytest."""
    print_header("Running Tests (pytest)")

    # Run pytest with coverage
    success = run_command(
        ["pytest", "-v", "--tb=short", "--cov=app", "--cov=routers", "--cov=config",
         "--cov-report=term-missing", "tests/"],
        "Pytest test suite",
        allow_failure=False
    )

    return success


def log_results(passed, failed):
    """Log validation results to logs folder."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().isoformat()
    log_file = log_dir / f"pre_push_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    log_data = {
        "timestamp": timestamp,
        "passed": passed,
        "failed": failed,
        "total": len(passed) + len(failed),
        "success": len(failed) == 0
    }

    with open(log_file, 'w') as f:
        json.dump(log_data, f, indent=2)

    print_info(f"Results logged to: {log_file}")


def main():
    """Main validation function."""
    print_header("Pre-Push Validation")
    print_info(f"Starting validation at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    passed_checks = []
    failed_checks = []

    # Check dependencies
    if not check_dependencies():
        print_warning("\nSome dependencies are missing, but continuing with available tools...")

    # Run linting
    try:
        if run_linting():
            passed_checks.append("linting")
        else:
            failed_checks.append("linting")
    except SystemExit:
        failed_checks.append("linting")
        log_results(passed_checks, failed_checks)
        sys.exit(1)

    # Run formatting check
    try:
        if run_formatting():
            passed_checks.append("formatting")
        else:
            failed_checks.append("formatting")
    except SystemExit:
        failed_checks.append("formatting")
        log_results(passed_checks, failed_checks)
        sys.exit(1)

    # Run tests
    try:
        if run_tests():
            passed_checks.append("tests")
        else:
            failed_checks.append("tests")
    except SystemExit:
        failed_checks.append("tests")
        log_results(passed_checks, failed_checks)
        sys.exit(1)

    # Log results
    log_results(passed_checks, failed_checks)

    # Final summary
    print_header("Validation Summary")

    if failed_checks:
        print_error(f"Failed checks: {', '.join(failed_checks)}")
        print_error("\n❌ Push blocked! Please fix the issues above.")
        sys.exit(1)
    else:
        print_success(f"All checks passed: {', '.join(passed_checks)}")
        print_success("\n✅ Code is ready to push!")
        sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_error("\n\nValidation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
