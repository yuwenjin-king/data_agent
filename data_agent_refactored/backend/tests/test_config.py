import pytest

from app.core.config import Settings


def _set_valid_production_env(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("CRYPTO_KEY", "0BSNIO-vn73OLi4xanEhjZlPXjfmo0RJR8Y7f1Q01DA=")
    monkeypatch.setenv("JWT_SECRET_KEY", "stable-jwt-secret")
    monkeypatch.setenv("ADMIN_PASSWORD", "strong-admin-password")
    monkeypatch.setenv("CODE_EXECUTOR_TYPE", "docker")


def test_development_settings_allow_dev_defaults(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("AUTH_ENABLED", "false")
    monkeypatch.setenv("CRYPTO_KEY", "")
    monkeypatch.setenv("JWT_SECRET_KEY", "")
    monkeypatch.setenv("ADMIN_PASSWORD", "")
    monkeypatch.setenv("CODE_EXECUTOR_TYPE", "local")

    config = Settings()

    assert config.APP_ENV == "development"
    assert config.AUTH_ENABLED is False


def test_production_requires_stable_secrets(monkeypatch):
    _set_valid_production_env(monkeypatch)
    monkeypatch.setenv("CRYPTO_KEY", "")

    with pytest.raises(ValueError, match="CRYPTO_KEY"):
        Settings()


def test_production_requires_auth_enabled(monkeypatch):
    _set_valid_production_env(monkeypatch)
    monkeypatch.setenv("AUTH_ENABLED", "false")

    with pytest.raises(ValueError, match="AUTH_ENABLED=true"):
        Settings()


def test_production_rejects_local_code_executor_by_default(monkeypatch):
    _set_valid_production_env(monkeypatch)
    monkeypatch.setenv("CODE_EXECUTOR_TYPE", "local")
    monkeypatch.setenv("ALLOW_LOCAL_CODE_EXECUTOR_IN_PRODUCTION", "false")

    with pytest.raises(ValueError, match="CODE_EXECUTOR_TYPE=local"):
        Settings()


def test_production_can_explicitly_allow_local_code_executor(monkeypatch):
    _set_valid_production_env(monkeypatch)
    monkeypatch.setenv("CODE_EXECUTOR_TYPE", "local")
    monkeypatch.setenv("ALLOW_LOCAL_CODE_EXECUTOR_IN_PRODUCTION", "true")

    config = Settings()

    assert config.CODE_EXECUTOR_TYPE == "local"
