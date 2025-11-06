#!/usr/bin/env bash
#
# Pre-commit hook that runs validation checks before allowing commits.
# This hook runs the pre_push_check.py script to ensure code quality.
#
# To bypass this hook (not recommended), use: git commit --no-verify
#

echo "Running pre-commit validation..."

# Run the pre-push check script
python scripts/pre_push_check.py

# Capture the exit code
RESULT=$?

# If validation failed, prevent the commit
if [ $RESULT -ne 0 ]; then
    echo ""
    echo "❌ Pre-commit validation failed. Commit blocked."
    echo "Fix the issues above or use 'git commit --no-verify' to bypass (not recommended)."
    exit 1
fi

echo "✅ Pre-commit validation passed!"
exit 0
