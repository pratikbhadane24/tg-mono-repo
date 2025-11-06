# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-11-06

### Restructure - Production-Grade Repository Setup

#### Added
- **New Directory Structure**: Reorganized repository into production-grade layout
  - `app/`: Core application logic (bot_api, service, manager, models, scheduler, database, cli)
  - `routers/`: FastAPI route handlers
  - `config/`: Configuration management
  - `docs/`: Comprehensive documentation (api.md, setup.md, user-guide.md)
  - `scripts/`: Utility scripts (pre_push_check.py)
  - `logs/`: Change tracking and validation logs
  - `.github/agents/`: Instructions for AI agents

- **Documentation**: Complete documentation suite
  - API documentation with full endpoint details and examples
  - Setup guide with step-by-step instructions
  - User guide covering all features and troubleshooting

- **Testing Infrastructure**: Production-grade test suite
  - Unit tests for models, configuration
  - Integration tests for API endpoints
  - Test configuration in pyproject.toml
  - Code coverage reporting

- **Pre-Push Validation**: Automated quality checks before pushing
  - Python script (`scripts/pre_push_check.py`) runs linting, formatting, and tests
  - Git pre-push hook automatically installed
  - Results logged to `logs/` folder
  - Blocks push if any check fails

- **Code Quality Tools**:
  - Ruff for linting
  - Black for formatting
  - Pytest for testing with coverage
  - Configuration in pyproject.toml

#### Changed
- **Docker**: Optimized Dockerfile to use `uv` for faster dependency installation
  - Multi-stage build for smaller image size
  - Health check added
  - More efficient layer caching

- **Imports**: Migrated all imports to use new structure
  - `from app.models import ...` instead of `from telegram.models import ...`
  - `from config.settings import ...` instead of `from telegram.config import ...`
  - `from routers import ...` for route handlers

- **Requirements**: Added testing and code quality dependencies
  - pytest, pytest-asyncio, pytest-cov, pytest-mock
  - ruff, black

- **Project Configuration**: Enhanced pyproject.toml
  - Pytest configuration with markers (unit, integration, slow)
  - Coverage configuration
  - Ruff and Black settings

#### Deprecated
- **telegram/ folder**: Old structure is deprecated
  - New code should go in `app/`, `routers/`, `config/`
  - Old folder kept temporarily for reference
  - Will be removed in future version

#### Documentation
- Created comprehensive API documentation (docs/api.md)
- Created detailed setup guide (docs/setup.md)
- Created user guide with troubleshooting (docs/user-guide.md)
- Added agent instructions (.github/agents/instructions.md)

#### Infrastructure
- Pre-push git hook for automated validation
- Python validation script with colored output
- Logs folder for tracking changes and validation results
- .gitignore updated for new structure

### Migration Guide

To update your code to use the new structure:

1. **Update imports**:
   ```python
   # Old
   from telegram import TelegramManager
   from telegram.config import get_telegram_config
   
   # New
   from app import TelegramManager
   from config import get_telegram_config
   ```

2. **Update CLI usage**:
   ```bash
   # Old
   python -m telegram.cli add -1001234567890 "Channel"
   
   # New
   python -m app.cli add -1001234567890 "Channel"
   ```

3. **No changes needed for**:
   - Environment variables (.env file)
   - Docker usage
   - API endpoints
   - Database structure

## [1.0.0] - 2024-XX-XX

### Initial Release
- FastAPI service for Telegram paid access management
- MongoDB integration
- Invite link generation
- Join request handling
- Membership expiration tracking
- Scheduler for cleanup
- CLI for channel management
- Basic documentation

---

## Change Types

- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Features that will be removed in future versions
- **Removed**: Features that have been removed
- **Fixed**: Bug fixes
- **Security**: Security improvements
