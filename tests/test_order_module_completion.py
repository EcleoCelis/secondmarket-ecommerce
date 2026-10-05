from pathlib import Path

from backend.app import create_app
from backend.app.core.config import TestingConfig


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_module_07_roadmap_marks_required_steps_complete():
    roadmap = (PROJECT_ROOT / "backend" / "docs" / "modules" / "modules.md").read_text(encoding="utf-8")

    assert "| 07 | Order & Fulfillment Management | Order creation, buyer order history, admin order list, status updates, cancellation rules, and fulfillment tracking. | Complete |" in roadmap
    assert "Step 1 - Order API Foundation" in roadmap
    assert "Step 2 - Buyer Order Frontend Folder and Page Foundation" in roadmap
    assert "Step 3 - Buyer Order Frontend API Integration" in roadmap
    assert "Step 4 - Admin Order Management Frontend Foundation" in roadmap
    assert "Step 5 - Fulfillment Status Update API" in roadmap
    assert "Step 6 - Cancellation Rules and Buyer Tracking" in roadmap
    assert "Step 7 - Module 07 Completion Check" in roadmap


def test_module_07_frontend_assets_remain_modular():
    required_files = [
        "frontend/orders/index.html",
        "frontend/orders/pages/history.html",
        "frontend/orders/pages/detail.html",
        "frontend/static/css/orders/base.css",
        "frontend/static/js/orders/orders-api.js",
        "frontend/static/js/orders/app.js",
        "frontend/static/js/orders/pages/history-page.js",
        "frontend/static/js/orders/pages/detail-page.js",
        "frontend/admin/pages/orders.html",
        "frontend/static/js/admin/pages/orders-page.js",
    ]

    for relative_path in required_files:
        assert (PROJECT_ROOT / relative_path).is_file()


def test_module_07_backend_contracts_are_registered_and_guarded():
    app = create_app(TestingConfig)
    client = app.test_client()

    buyer_list = client.get("/api/v1/orders")
    buyer_detail = client.get("/api/v1/orders/SM-EXAMPLE")
    buyer_cancel = client.patch("/api/v1/orders/SM-EXAMPLE/cancel")
    admin_list = client.get("/api/v1/admin/orders")
    admin_detail = client.get("/api/v1/admin/orders/SM-EXAMPLE")
    admin_fulfillment = client.patch("/api/v1/admin/orders/SM-EXAMPLE/fulfillment", json={"order_status": "processing"})

    assert buyer_list.status_code == 401
    assert buyer_detail.status_code == 401
    assert buyer_cancel.status_code == 401
    assert admin_list.status_code == 401
    assert admin_detail.status_code == 401
    assert admin_fulfillment.status_code == 401


def test_module_07_frontend_shells_and_clients_are_reachable():
    app = create_app(TestingConfig)
    client = app.test_client()

    orders_shell = client.get("/orders")
    orders_api_client = client.get("/static/js/orders/orders-api.js")
    orders_app = client.get("/static/js/orders/app.js")
    orders_detail_page = client.get("/static/js/orders/pages/detail-page.js")
    admin_shell = client.get("/admin")
    admin_api_client = client.get("/static/js/admin/admin-api.js")
    admin_orders_page = client.get("/static/js/admin/pages/orders-page.js")

    assert orders_shell.status_code == 200
    assert "Orders | SecondMarket" in orders_shell.get_data(as_text=True)
    assert "/static/js/orders/app.js" in orders_shell.get_data(as_text=True)

    orders_javascript = orders_api_client.get_data(as_text=True)
    assert orders_api_client.status_code == 200
    assert 'const BASE_URL = "/api/v1/orders"' in orders_javascript
    assert "listOrders" in orders_javascript
    assert "getOrder" in orders_javascript
    assert "cancelOrder" in orders_javascript

    assert "cancelOrder" in orders_app.get_data(as_text=True)
    assert "renderTrackingPanel" in orders_detail_page.get_data(as_text=True)

    assert admin_shell.status_code == 200
    assert 'data-admin-nav="orders"' in admin_shell.get_data(as_text=True)
    assert "/static/js/admin/pages/orders-page.js" in admin_shell.get_data(as_text=True)

    admin_javascript = admin_api_client.get_data(as_text=True)
    assert admin_api_client.status_code == 200
    assert "listOrders" in admin_javascript
    assert "getOrder" in admin_javascript
    assert "renderOrdersPage" in admin_orders_page.get_data(as_text=True)
