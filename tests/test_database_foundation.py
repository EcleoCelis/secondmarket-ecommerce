from backend.app import create_app
from backend.app.core.config import BaseConfig, TestingConfig, normalize_database_url
from backend.app.extensions import db, migrate


def test_default_database_target_is_postgresql():
    assert BaseConfig.SQLALCHEMY_DATABASE_URI.startswith("postgresql+psycopg://")


def test_legacy_postgres_url_is_normalized_for_sqlalchemy():
    normalized = normalize_database_url("postgres://user:pass@localhost:5432/secondhand")

    assert normalized == "postgresql+psycopg://user:pass@localhost:5432/secondhand"


def test_database_extension_is_registered_with_app():
    app = create_app(TestingConfig)

    assert "sqlalchemy" in app.extensions
    with app.app_context():
        assert db.engine is not None


def test_migration_extension_is_registered_with_app():
    app = create_app(TestingConfig)

    assert "migrate" in app.extensions
    assert migrate.db is db


def test_test_database_can_create_and_drop_schema():
    app = create_app(TestingConfig)

    with app.app_context():
        db.create_all()
        assert {"users", "auth_sessions"}.issubset(db.metadata.tables.keys())
        db.drop_all()
