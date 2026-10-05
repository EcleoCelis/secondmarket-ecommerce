from backend.app import create_app
from backend.app.core.config import TestingConfig
from backend.app.extensions import db
from backend.app.models import Category, Product, User
from backend.app.seed import seed_development_data


def test_development_seed_data_is_idempotent():
    app = create_app(TestingConfig)

    with app.app_context():
        db.create_all()

        first = seed_development_data()
        second = seed_development_data()

        assert first == {"users": 1, "categories": 4, "products": 8}
        assert second == {"users": 0, "categories": 0, "products": 0}
        assert User.query.filter_by(email="admin@secondmarket.test").count() == 1
        assert Category.query.count() == 4
        assert Product.query.count() == 8

        db.session.remove()
        db.drop_all()


def test_seed_dev_cli_command_creates_starter_data():
    app = create_app(TestingConfig)
    runner = app.test_cli_runner()

    result = runner.invoke(args=["seed-dev"])

    assert result.exit_code == 0
    assert "Seed complete. Created users=1, categories=4, products=8." in result.output

    with app.app_context():
        assert User.query.filter_by(email="admin@secondmarket.test").count() == 1
        assert Category.query.filter_by(slug="furniture").count() == 1
        assert Product.query.filter_by(slug="pre-owned-wireless-headphones").count() == 1
        db.session.remove()
        db.drop_all()
