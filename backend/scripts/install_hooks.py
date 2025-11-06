#!/usr/bin/env python3
"""
Install git hooks for the project.

This script sets up pre-commit hooks that run validation checks
before allowing commits.
"""

import os
import shutil
import sys
from pathlib import Path


def main():
    """Install git hooks."""
    # Get project root
    script_dir = Path(__file__).parent.absolute()
    project_root = script_dir.parent

    # Paths
    hooks_dir = project_root / ".git" / "hooks"
    pre_commit_template = script_dir / "pre-commit-hook.sh"
    pre_commit_dest = hooks_dir / "pre-commit"

    if not hooks_dir.exists():
        print("❌ Error: .git/hooks directory not found")
        print("   Make sure you're in a git repository")
        sys.exit(1)

    # Check if hook template exists
    if not pre_commit_template.exists():
        print("❌ Error: pre-commit-hook.sh template not found")
        print(f"   Expected at: {pre_commit_template}")
        sys.exit(1)

    # Copy hook to .git/hooks
    print(f"Installing pre-commit hook to {pre_commit_dest}...")
    shutil.copy2(pre_commit_template, pre_commit_dest)

    # Make executable
    os.chmod(pre_commit_dest, 0o755)

    print("✅ Git hooks installed successfully!")
    print()
    print("The following hooks are now active:")
    print("  - pre-commit: Runs linting, formatting checks, and tests")
    print()
    print("To bypass hooks (not recommended), use: git commit --no-verify")


if __name__ == "__main__":
    main()
