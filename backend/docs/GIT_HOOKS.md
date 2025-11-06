# Git Hooks Setup

This project uses git hooks to ensure code quality before commits.

## Installation

To install the git hooks, run:

```bash
python scripts/install_hooks.py
```

This will install a pre-commit hook that runs:
- Code linting with `ruff`
- Code formatting checks with `black`
- All tests with `pytest`

## What Happens

When you try to commit code, the pre-commit hook will:

1. **Run Linting**: Check code style and common errors with `ruff`
2. **Check Formatting**: Verify code formatting with `black`
3. **Run Tests**: Execute all tests with `pytest`

If any of these checks fail, the commit will be blocked.

## Bypassing the Hook

In rare cases where you need to commit without running the checks (NOT RECOMMENDED), you can use:

```bash
git commit --no-verify
```

**Warning**: Only bypass the hook if absolutely necessary. The checks are there to maintain code quality.

## Manual Checks

You can also run the checks manually at any time:

```bash
# Run all checks
python scripts/pre_push_check.py

# Or run individual tools
python -m ruff check app routers config tests main.py
python -m black --check app routers config tests main.py
python -m pytest tests/
```

## Fixing Issues

If the pre-commit hook fails:

1. **Linting errors**: Fix them manually or run `ruff check --fix app routers config tests main.py`
2. **Formatting errors**: Run `black app routers config tests main.py` to auto-format
3. **Test failures**: Fix the failing tests

Then try committing again.
