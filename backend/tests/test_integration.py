"""
Comprehensive integration tests for the application structure and imports.

This test module validates that all modules can be imported correctly and that
the application structure is sound. These tests catch issues that unit tests miss.
"""

import importlib
import inspect
import sys
from pathlib import Path

import pytest


class TestApplicationStructure:
    """Test the overall application structure and module imports."""

    def test_all_app_modules_importable(self):
        """Test that all modules in the app package can be imported without errors."""
        app_modules = [
            "app",
            "app.main",
            "app.manager",
            "app.cli",
            "app.timezone_utils",
            "app.api",
            "app.api.endpoints",
            "app.api.endpoints.health",
            "app.api.endpoints.telegram",
            "app.core",
            "app.core.auth",
            "app.core.config",
            "app.models",
            "app.models.telegram",
            "app.models.responses",
            "app.services",
            "app.services.bot_api",
            "app.services.telegram_service",
            "app.services.scheduler",
            "app.services.database",
        ]

        failed_imports = []
        for module_name in app_modules:
            try:
                importlib.import_module(module_name)
            except Exception as e:
                failed_imports.append((module_name, str(e)))

        assert not failed_imports, f"Failed to import modules: {failed_imports}"

    def test_no_old_structure_imports(self):
        """Verify no code imports from old structure (config/, routers/, utils/)."""
        forbidden_patterns = [
            "from config.",
            "from config import",
            "from routers.",
            "from routers import",
            "from utils.",
            "from utils import",
        ]

        app_dir = Path("app")
        violations = []

        for py_file in app_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            content = py_file.read_text()
            for pattern in forbidden_patterns:
                if pattern in content:
                    violations.append(f"{py_file}: contains '{pattern}'")

        assert not violations, f"Found old import patterns:\n" + "\n".join(violations)

    def test_main_entry_points_work(self):
        """Test that both main.py entry points work."""
        # Test backward-compatible entry point
        from main import app as app1

        assert app1 is not None
        assert hasattr(app1, "title")
        assert app1.title == "Telegram Service"

        # Test new structure entry point
        from app.main import app as app2

        assert app2 is not None
        assert app1 is app2  # Should be the same instance

    def test_core_exports(self):
        """Test that core modules export expected components."""
        from app.core import TelegramConfig, get_telegram_config
        from app.core.auth import get_current_user, verify_user_token

        assert callable(get_telegram_config)
        assert callable(get_current_user)
        assert callable(verify_user_token)
        assert inspect.isclass(TelegramConfig)

    def test_models_exports(self):
        """Test that models package exports all expected models."""
        from app.models import (
            Audit,
            Channel,
            ErrorDetail,
            Invite,
            Membership,
            PyObjectId,
            StandardResponse,
            TelegramUser,
            utcnow,
        )

        expected_classes = [
            TelegramUser,
            Channel,
            Membership,
            Invite,
            Audit,
            StandardResponse,
            ErrorDetail,
        ]

        for cls in expected_classes:
            assert inspect.isclass(cls), f"{cls.__name__} should be a class"

        assert callable(utcnow)
        assert PyObjectId is not None

    def test_services_exports(self):
        """Test that services package exports all expected services."""
        from app.services import (
            MembershipScheduler,
            TelegramBotAPI,
            TelegramMembershipService,
            create_telegram_indexes,
            initialize_telegram_database,
        )

        assert inspect.isclass(TelegramBotAPI)
        assert inspect.isclass(TelegramMembershipService)
        assert inspect.isclass(MembershipScheduler)
        assert callable(create_telegram_indexes)
        assert callable(initialize_telegram_database)

    def test_api_endpoints_exist(self):
        """Test that API endpoints are properly registered."""
        from app.main import app

        routes = [route.path for route in app.routes if hasattr(route, "path")]

        # Check critical endpoints exist
        assert "/health" in routes
        assert "/" in routes
        # The telegram router adds routes dynamically, check that routes were added
        assert len(routes) > 5  # Should have more than just docs routes

    def test_no_circular_imports(self):
        """Test that importing all modules doesn't cause circular import issues."""
        modules_to_test = [
            "app.main",
            "app.manager",
            "app.services.telegram_service",
            "app.services.bot_api",
            "app.services.scheduler",
            "app.api.endpoints.telegram",
            "app.api.endpoints.health",
        ]

        for module_name in modules_to_test:
            # Clear the module from cache
            if module_name in sys.modules:
                del sys.modules[module_name]

            # Try to import fresh
            try:
                importlib.import_module(module_name)
            except ImportError as e:
                pytest.fail(f"Circular import detected in {module_name}: {e}")

    def test_config_singleton_behavior(self):
        """Test that config uses singleton pattern correctly."""
        from app.core.config import get_telegram_config

        config1 = get_telegram_config()
        config2 = get_telegram_config()

        assert config1 is config2, "Config should return the same instance"

    def test_all_dependencies_importable(self):
        """Test that all required external dependencies can be imported."""
        required_deps = [
            "fastapi",
            "pydantic",
            "motor",
            "httpx",
            "jose",
            "pytest",
            "ruff",
            "black",
        ]

        missing = []
        for dep in required_deps:
            try:
                importlib.import_module(dep)
            except ImportError:
                missing.append(dep)

        assert not missing, f"Missing required dependencies: {missing}"

    def test_manager_can_be_instantiated(self):
        """Test that TelegramManager can be imported and has correct interface."""
        from app.manager import TelegramManager

        assert inspect.isclass(TelegramManager)

        # Check it has expected methods
        expected_methods = [
            "initialize",
            "shutdown",
            "get_service",
            "get_bot",
            "get_scheduler",
        ]

        for method in expected_methods:
            assert hasattr(TelegramManager, method), f"Manager should have {method}"


class TestApplicationConfiguration:
    """Test that application configuration is properly set up."""

    def test_env_variables_loaded(self, test_env):
        """Test that test environment variables are properly loaded."""
        import os

        assert os.getenv("TELEGRAM_BOT_TOKEN") is not None
        assert os.getenv("JWT_SECRET_KEY") is not None

    def test_config_validation(self):
        """Test that config validates required fields."""
        from app.core.config import TelegramConfig
        from pydantic import ValidationError

        # Test that missing JWT_SECRET_KEY raises error (it's required now)
        import os

        # Temporarily remove JWT_SECRET_KEY
        old_jwt_key = os.environ.get("JWT_SECRET_KEY")
        if "JWT_SECRET_KEY" in os.environ:
            del os.environ["JWT_SECRET_KEY"]

        try:
            with pytest.raises(ValidationError):
                TelegramConfig(
                    TELEGRAM_BOT_TOKEN="test",
                    TELEGRAM_WEBHOOK_SECRET_PATH="test",
                    BASE_URL="https://test.com",
                    # JWT_SECRET_KEY is missing and required
                )
        finally:
            # Restore
            if old_jwt_key:
                os.environ["JWT_SECRET_KEY"] = old_jwt_key

    def test_jwt_config_present(self):
        """Test that JWT configuration is properly set."""
        from app.core.config import get_telegram_config

        config = get_telegram_config()

        assert hasattr(config, "JWT_SECRET_KEY")
        assert hasattr(config, "JWT_ALGORITHM")
        assert config.JWT_SECRET_KEY is not None
        assert config.JWT_ALGORITHM == "HS256"


class TestApplicationStartup:
    """Test that the application can start up correctly."""

    def test_fastapi_app_created(self):
        """Test that FastAPI app is created with correct settings."""
        from app.main import app

        assert app.title == "Telegram Service"
        assert app.version == "1.0.0"
        assert "Standalone service" in app.description

    def test_middleware_configured(self):
        """Test that CORS middleware is configured."""
        from app.main import app

        # Check that middleware is present
        assert len(app.user_middleware) > 0

    def test_lifespan_context_exists(self):
        """Test that lifespan context manager is defined."""
        from app.main import lifespan

        assert callable(lifespan)
        # lifespan is decorated with @asynccontextmanager which wraps it
        # We just need to verify it's callable and can be used as a context manager
        import inspect

        # The decorator makes it a regular function that returns an async generator
        assert inspect.isfunction(lifespan)
