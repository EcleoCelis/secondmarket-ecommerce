from pathlib import Path

from backend.app import create_app
from backend.app.core.config import TestingConfig


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_module_04_roadmap_marks_required_steps_complete():
    roadmap = (PROJECT_ROOT / "backend" / "docs" / "modules" / "modules.md").read_text(encoding="utf-8")

    assert "| 04 | Buyer Marketplace |" in roadmap
    assert "| 04 | Buyer Marketplace | Product catalog, category browsing, product details, search, filtering, sorting, wishlist, and responsive marketplace layout. | Complete |" in roadmap
    assert "Step 1 - Marketplace API and Product Image Foundation" in roadmap
    assert "Step 2 - Storefront API Integration" in roadmap
    assert "Step 3 - Marketplace UI Polish and Responsive Verification" in roadmap
    assert "Step 4 - Marketplace Search and Filter API Integration" in roadmap
    assert "Step 5 - Wishlist Persistence Preparation" in roadmap
    assert "Step 6 - Marketplace Final Review and Module 04 Completion Check" in roadmap


def test_wishlist_items_are_included_in_migration_history():
    migration = (
        PROJECT_ROOT / "migrations" / "versions" / "20261004_01_add_wishlist_items.py"
    ).read_text(encoding="utf-8")

    assert 'revision = "20261004_01"' in migration
    assert 'down_revision = "e559bbb96325"' in migration
    assert '"wishlist_items"' in migration
    assert "uq_wishlist_items_user_product" in migration
    assert "ix_wishlist_items_user_id" in migration
    assert "ix_wishlist_items_product_id" in migration


def test_module_04_frontend_and_api_assets_are_reachable():
    app = create_app(TestingConfig)
    client = app.test_client()

    storefront_response = client.get("/")
    marketplace_client_response = client.get("/static/js/marketplace-api.js")

    assert storefront_response.status_code == 200
    assert marketplace_client_response.status_code == 200
    assert "SecondMarketMarketplaceAPI" in marketplace_client_response.get_data(as_text=True)
