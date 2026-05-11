"""
Tests for Story 1.1: Monorepo Scaffold & Docker Compose

Tests verify:
- AC3: Required directory/file structure exists
- AC4: frontend/package.json was created with create-next-app options
- AC5: .env.example contains all required variables
- AC6: Dockerfile and Dockerfile.worker have correct content
"""
import json
import os

import pytest

# Project root is 2 levels up from backend/tests/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKEND_ROOT = os.path.join(PROJECT_ROOT, "backend")
FRONTEND_ROOT = os.path.join(PROJECT_ROOT, "frontend")


class TestMonorepoStructure:
    """AC3: Required directory structure exists."""

    def test_backend_directory_exists(self):
        assert os.path.isdir(BACKEND_ROOT)

    def test_frontend_directory_exists(self):
        assert os.path.isdir(FRONTEND_ROOT)

    def test_docker_compose_exists(self):
        assert os.path.isfile(os.path.join(PROJECT_ROOT, "docker-compose.yml"))

    def test_env_example_exists(self):
        assert os.path.isfile(os.path.join(PROJECT_ROOT, ".env.example"))

    def test_readme_exists(self):
        assert os.path.isfile(os.path.join(PROJECT_ROOT, "README.md"))

    def test_devcontainer_json_exists(self):
        assert os.path.isfile(
            os.path.join(PROJECT_ROOT, ".devcontainer", "devcontainer.json")
        )

    def test_github_workflows_directory_exists(self):
        assert os.path.isdir(os.path.join(PROJECT_ROOT, ".github", "workflows"))


class TestBackendPackageStructure:
    """AC3: Backend package structure with __init__.py files."""

    @pytest.mark.parametrize("pkg_path", [
        "app/__init__.py",
        "app/api/__init__.py",
        "app/api/v1/__init__.py",
        "app/core/__init__.py",
        "app/db/__init__.py",
        "app/auth/__init__.py",
        "app/scraping/__init__.py",
        "app/billing/__init__.py",
        "app/notifications/__init__.py",
        "workers/__init__.py",
        "tests/__init__.py",
    ])
    def test_init_file_exists(self, pkg_path):
        full_path = os.path.join(BACKEND_ROOT, pkg_path.replace("/", os.sep))
        assert os.path.isfile(full_path), f"Missing: backend/{pkg_path}"

    def test_main_py_exists(self):
        assert os.path.isfile(os.path.join(BACKEND_ROOT, "app", "main.py"))

    def test_config_py_exists(self):
        assert os.path.isfile(os.path.join(BACKEND_ROOT, "app", "core", "config.py"))

    def test_alembic_ini_exists(self):
        assert os.path.isfile(os.path.join(BACKEND_ROOT, "alembic.ini"))

    def test_alembic_env_py_exists(self):
        assert os.path.isfile(os.path.join(BACKEND_ROOT, "alembic", "env.py"))

    def test_alembic_versions_dir_exists(self):
        assert os.path.isdir(os.path.join(BACKEND_ROOT, "alembic", "versions"))

    def test_playwright_pool_placeholder_exists(self):
        assert os.path.isfile(os.path.join(BACKEND_ROOT, "workers", "playwright_pool.py"))


class TestFrontendPackageJson:
    """AC4: package.json created with correct create-next-app options."""

    @pytest.fixture(autouse=True)
    def load_package_json(self):
        pkg_path = os.path.join(FRONTEND_ROOT, "package.json")
        assert os.path.isfile(pkg_path), "frontend/package.json not found"
        with open(pkg_path) as f:
            self.pkg = json.load(f)

    def test_next_dependency_exists(self):
        deps = {**self.pkg.get("dependencies", {}), **self.pkg.get("devDependencies", {})}
        assert "next" in deps, "next not in dependencies"

    def test_typescript_dependency_exists(self):
        dev_deps = self.pkg.get("devDependencies", {})
        assert "typescript" in dev_deps or "@types/react" in dev_deps

    def test_tailwind_dependency_exists(self):
        dev_deps = self.pkg.get("devDependencies", {})
        assert "tailwindcss" in dev_deps

    def test_src_dir_exists(self):
        assert os.path.isdir(os.path.join(FRONTEND_ROOT, "src")), \
            "frontend/src/ directory not found (--src-dir flag)"

    def test_app_router_dir_exists(self):
        assert os.path.isdir(os.path.join(FRONTEND_ROOT, "src", "app")), \
            "frontend/src/app/ not found (App Router)"

    def test_frontend_dockerfile_exists(self):
        assert os.path.isfile(os.path.join(FRONTEND_ROOT, "Dockerfile"))


class TestEnvExample:
    """AC5: .env.example contains all required environment variables."""

    @pytest.fixture(autouse=True)
    def load_env_example(self):
        env_path = os.path.join(PROJECT_ROOT, ".env.example")
        with open(env_path) as f:
            self.content = f.read()

    @pytest.mark.parametrize("var", [
        "DATABASE_URL",
        "REDIS_URL",
        "SECRET_KEY",
        "SENTRY_DSN",
        "RESEND_API_KEY",
        "STRIPE_SECRET_KEY",
    ])
    def test_required_var_present(self, var):
        assert var in self.content, f"{var} missing from .env.example"


class TestDockerfiles:
    """AC6: Dockerfile and Dockerfile.worker have correct content."""

    def test_dockerfile_uses_python313(self):
        path = os.path.join(BACKEND_ROOT, "Dockerfile")
        with open(path) as f:
            content = f.read()
        assert "python:3.13" in content

    def test_dockerfile_has_uvicorn_cmd(self):
        path = os.path.join(BACKEND_ROOT, "Dockerfile")
        with open(path) as f:
            content = f.read()
        assert "uvicorn" in content

    def test_dockerfile_worker_has_playwright_install(self):
        path = os.path.join(BACKEND_ROOT, "Dockerfile.worker")
        with open(path) as f:
            content = f.read()
        assert "playwright install chromium" in content

    def test_frontend_dockerfile_uses_node20(self):
        path = os.path.join(FRONTEND_ROOT, "Dockerfile")
        with open(path) as f:
            content = f.read()
        assert "node:20" in content


class TestAlembicConfig:
    """Alembic uses settings.DATABASE_URL, not os.environ.get() directly."""

    def test_alembic_env_imports_settings(self):
        path = os.path.join(BACKEND_ROOT, "alembic", "env.py")
        with open(path) as f:
            content = f.read()
        assert "from app.core.config import settings" in content

    def test_alembic_env_sets_main_option(self):
        path = os.path.join(BACKEND_ROOT, "alembic", "env.py")
        with open(path) as f:
            content = f.read()
        assert "config.set_main_option" in content
        assert "settings.DATABASE_URL" in content


class TestDockerCompose:
    """AC1: docker-compose.yml has all 5 required services."""

    @pytest.fixture(autouse=True)
    def load_compose(self):
        import yaml
        compose_path = os.path.join(PROJECT_ROOT, "docker-compose.yml")
        with open(compose_path) as f:
            self.compose = yaml.safe_load(f)

    def test_api_service_exists(self):
        assert "api" in self.compose["services"]

    def test_worker_service_exists(self):
        assert "worker" in self.compose["services"]

    def test_frontend_service_exists(self):
        assert "frontend" in self.compose["services"]

    def test_db_service_uses_postgres16(self):
        assert "db" in self.compose["services"]
        assert "postgres:16" in self.compose["services"]["db"]["image"]

    def test_redis_service_exists(self):
        assert "redis" in self.compose["services"]

    def test_api_port_8000(self):
        ports = self.compose["services"]["api"].get("ports", [])
        assert any("8000" in str(p) for p in ports)

    def test_frontend_port_3000(self):
        ports = self.compose["services"]["frontend"].get("ports", [])
        assert any("3000" in str(p) for p in ports)

    def test_db_health_check_configured(self):
        db = self.compose["services"]["db"]
        assert "healthcheck" in db

    def test_postgres_data_volume_defined(self):
        assert "postgres_data" in self.compose.get("volumes", {})
