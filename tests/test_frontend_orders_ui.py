from backend.app import create_app
from backend.app.core.config import TestingConfig


def test_orders_frontend_shell_is_served_separately():
    app = create_app(TestingConfig)

    response = app.test_client().get("/orders")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Orders | SecondMarket" in html
    assert "/static/css/orders/base.css" in html
    assert "/static/js/auth-client.js" in html
    assert "/static/js/orders/orders-api.js" in html
    assert "/static/js/orders/app.js" in html
    assert "/static/js/orders/pages/history-page.js" in html
    assert "/static/js/orders/pages/detail-page.js" in html
    assert "orders-main-content" in html
    assert "frontend/static/js/checkout" not in html


def test_orders_frontend_assets_are_served_separately():
    app = create_app(TestingConfig)
    client = app.test_client()

    expected_assets = {
        "/static/css/orders/base.css": ".orders-filter-bar",
        "/static/js/orders/orders-api.js": "SecondMarketOrdersAPI",
        "/static/js/orders/app.js": "class SecondMarketOrdersApp",
        "/static/js/orders/pages/history-page.js": "renderHistoryPage",
        "/static/js/orders/pages/detail-page.js": "renderDetailPage",
    }

    for asset_path, expected_text in expected_assets.items():
        response = client.get(asset_path)
        assert response.status_code == 200
        assert expected_text in response.get_data(as_text=True)


def test_orders_page_templates_are_served_separately():
    app = create_app(TestingConfig)
    client = app.test_client()

    expected_templates = {
        "/orders/pages/history.html": "{{orderCards}}",
        "/orders/pages/detail.html": "{{orderItems}}",
    }

    for template_path, expected_text in expected_templates.items():
        response = client.get(template_path)
        assert response.status_code == 200
        assert expected_text in response.get_data(as_text=True)

    history_template = client.get("/orders/pages/history.html").get_data(as_text=True)
    assert "ordersApp.applyFilters(event)" in history_template
    assert "{{statusOptions}}" in history_template

    detail_template = client.get("/orders/pages/detail.html").get_data(as_text=True)
    assert "Back To History" in detail_template
    assert "{{shippingAddress}}" in detail_template
    assert "{{trackingPanel}}" in detail_template
    assert "{{cancellationAction}}" in detail_template


def test_orders_frontend_client_targets_order_api_contract():
    app = create_app(TestingConfig)
    client = app.test_client()

    javascript = client.get("/static/js/orders/orders-api.js").get_data(as_text=True)
    app_js = client.get("/static/js/orders/app.js").get_data(as_text=True)
    history_page_js = client.get("/static/js/orders/pages/history-page.js").get_data(as_text=True)
    detail_page_js = client.get("/static/js/orders/pages/detail-page.js").get_data(as_text=True)

    assert 'const BASE_URL = "/api/v1/orders"' in javascript
    assert "listOrders" in javascript
    assert "getOrder" in javascript
    assert "cancelOrder" in javascript
    assert "buildQueryString" in javascript
    assert "SecondMarketAuthAPI.me" in app_js
    assert "role !== \"buyer\"" in app_js
    assert "refreshOrders" in app_js
    assert "loadOrder" in app_js
    assert "cancelOrder" in app_js
    assert "showToast" in app_js
    assert "initialOrderNumber" in app_js
    assert "URLSearchParams(window.location.search)" in app_js
    assert "window.history.replaceState" in app_js
    assert "/orders/pages/${templateName}.html" in app_js
    assert "renderHistoryPage" in history_page_js
    assert "ordersApp.loadOrder" in history_page_js
    assert "renderDetailPage" in detail_page_js
    assert "renderTrackingPanel" in detail_page_js
    assert "ordersApp.cancelOrder" in detail_page_js
