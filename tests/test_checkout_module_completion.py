from pathlib import Path

from backend.app import create_app
from backend.app.core.config import TestingConfig


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_module_06_roadmap_marks_required_steps_complete():
    roadmap = (PROJECT_ROOT / "backend" / "docs" / "modules" / "modules.md").read_text(encoding="utf-8")

    assert "| 06 | Cart & Checkout | Cart persistence, item availability validation, order summary, address capture, payment method selection, and checkout confirmation. | Complete |" in roadmap
    assert "Step 1 - Cart API Foundation" in roadmap
    assert "Step 2 - Checkout Frontend Folder and Page Foundation" in roadmap
    assert "Step 3 - Cart Frontend API Integration" in roadmap
    assert "Step 4 - Checkout Validation and Order Draft API" in roadmap
    assert "Step 5 - Checkout Confirmation Workflow" in roadmap
    assert "Step 6 - Module 06 Completion Check" in roadmap


def test_module_06_frontend_assets_remain_modular():
    required_files = [
        "frontend/checkout/index.html",
        "frontend/checkout/pages/cart.html",
        "frontend/checkout/pages/summary.html",
        "frontend/static/css/checkout/base.css",
        "frontend/static/js/checkout/checkout-api.js",
        "frontend/static/js/checkout/app.js",
        "frontend/static/js/checkout/pages/cart-page.js",
        "frontend/static/js/checkout/pages/summary-page.js",
    ]

    for relative_path in required_files:
        assert (PROJECT_ROOT / relative_path).is_file()


def test_module_06_checkout_shell_and_api_contracts_are_reachable():
    app = create_app(TestingConfig)
    client = app.test_client()

    checkout_shell = client.get("/checkout")
    checkout_client = client.get("/static/js/checkout/checkout-api.js")
    checkout_app = client.get("/static/js/checkout/app.js")
    summary_page = client.get("/static/js/checkout/pages/summary-page.js")

    assert checkout_shell.status_code == 200
    assert "Checkout | SecondMarket" in checkout_shell.get_data(as_text=True)
    assert "/static/js/checkout/app.js" in checkout_shell.get_data(as_text=True)

    javascript = checkout_client.get_data(as_text=True)
    assert checkout_client.status_code == 200
    assert 'const BASE_URL = "/api/v1/cart"' in javascript
    assert 'const CHECKOUT_BASE_URL = "/api/v1/checkout"' in javascript
    assert "createDraft" in javascript
    assert "confirmOrder" in javascript

    assert "submitCheckout" in checkout_app.get_data(as_text=True)
    assert "checkoutPayloadFromForm" in checkout_app.get_data(as_text=True)
    assert "renderConfirmationPanel" in summary_page.get_data(as_text=True)
