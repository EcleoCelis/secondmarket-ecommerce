from pathlib import Path

from backend.app import create_app
from backend.app.core.config import TestingConfig


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_module_05_roadmap_marks_required_steps_complete():
    roadmap = (PROJECT_ROOT / "backend" / "docs" / "modules" / "modules.md").read_text(encoding="utf-8")

    assert "| 05 | Admin Seller Management | Admin product lifecycle, category management, product images, availability, item condition, and secondhand inventory workflow. | Complete |" in roadmap
    assert "Step 1 - Admin Seller API Foundation" in roadmap
    assert "Step 2 - Admin Frontend Folder and Page Foundation" in roadmap
    assert "Step 3 - Product Create and Edit API" in roadmap
    assert "Step 4 - Product Status and Inventory Workflow" in roadmap
    assert "Step 5 - Category Management Workflow" in roadmap
    assert "Step 6 - Admin Frontend API Integration Review" in roadmap
    assert "Step 7 - Admin Seller Management Final Review and Module 05 Completion Check" in roadmap


def test_module_05_admin_frontend_assets_remain_modular():
    required_files = [
        "frontend/admin/index.html",
        "frontend/admin/pages/dashboard.html",
        "frontend/admin/pages/products.html",
        "frontend/admin/pages/categories.html",
        "frontend/static/css/admin/base.css",
        "frontend/static/js/admin/admin-api.js",
        "frontend/static/js/admin/app.js",
        "frontend/static/js/admin/pages/dashboard-page.js",
        "frontend/static/js/admin/pages/products-page.js",
        "frontend/static/js/admin/pages/categories-page.js",
    ]

    for relative_path in required_files:
        assert (PROJECT_ROOT / relative_path).is_file()


def test_module_05_admin_shell_and_api_contracts_are_reachable():
    app = create_app(TestingConfig)
    client = app.test_client()

    admin_shell = client.get("/admin")
    admin_client = client.get("/static/js/admin/admin-api.js")

    assert admin_shell.status_code == 200
    assert "Admin Seller | SecondMarket" in admin_shell.get_data(as_text=True)
    assert "/static/js/admin/app.js" in admin_shell.get_data(as_text=True)

    javascript = admin_client.get_data(as_text=True)
    assert admin_client.status_code == 200
    assert 'const BASE_URL = "/api/v1/admin"' in javascript
    assert "listProducts" in javascript
    assert "createCategory" in javascript
    assert "updateCategoryStatus" in javascript
    assert "updateProductStatus" in javascript
    assert "updateProductInventory" in javascript
