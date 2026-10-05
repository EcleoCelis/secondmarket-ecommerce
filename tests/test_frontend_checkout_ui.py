from backend.app import create_app
from backend.app.core.config import TestingConfig


def test_checkout_frontend_shell_is_served_separately():
    app = create_app(TestingConfig)

    response = app.test_client().get("/checkout")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Checkout | SecondMarket" in html
    assert "/static/css/checkout/base.css" in html
    assert "/static/js/auth-client.js" in html
    assert "/static/js/checkout/checkout-api.js" in html
    assert "/static/js/checkout/app.js" in html
    assert "/static/js/checkout/pages/cart-page.js" in html
    assert "/static/js/checkout/pages/summary-page.js" in html
    assert "checkout-main-content" in html
    assert "frontend/static/js/admin" not in html


def test_checkout_frontend_assets_are_served_separately():
    app = create_app(TestingConfig)
    client = app.test_client()

    expected_assets = {
        "/static/css/checkout/base.css": ".checkout-layout",
        "/static/js/checkout/checkout-api.js": "SecondMarketCheckoutAPI",
        "/static/js/checkout/app.js": "class SecondMarketCheckoutApp",
        "/static/js/checkout/pages/cart-page.js": "renderCartPage",
        "/static/js/checkout/pages/summary-page.js": "renderSummaryPage",
    }

    for asset_path, expected_text in expected_assets.items():
        response = client.get(asset_path)
        assert response.status_code == 200
        assert expected_text in response.get_data(as_text=True)


def test_checkout_page_templates_are_served_separately():
    app = create_app(TestingConfig)
    client = app.test_client()

    expected_templates = {
        "/checkout/pages/cart.html": "{{cartItems}}",
        "/checkout/pages/summary.html": "{{cartSubtotal}}",
    }

    for template_path, expected_text in expected_templates.items():
        response = client.get(template_path)
        assert response.status_code == 200
        assert expected_text in response.get_data(as_text=True)

    cart_template = client.get("/checkout/pages/cart.html").get_data(as_text=True)
    assert "checkoutApp.navigate('summary')" in cart_template
    assert "{{checkoutDisabled}}" in cart_template

    summary_template = client.get("/checkout/pages/summary.html").get_data(as_text=True)
    assert "Shipping And Payment" in summary_template
    assert "Place Order" in summary_template


def test_checkout_frontend_client_targets_cart_api_contract():
    app = create_app(TestingConfig)
    client = app.test_client()

    javascript = client.get("/static/js/checkout/checkout-api.js").get_data(as_text=True)
    app_js = client.get("/static/js/checkout/app.js").get_data(as_text=True)
    cart_page_js = client.get("/static/js/checkout/pages/cart-page.js").get_data(as_text=True)
    summary_page_js = client.get("/static/js/checkout/pages/summary-page.js").get_data(as_text=True)

    assert 'const BASE_URL = "/api/v1/cart"' in javascript
    assert "getCart" in javascript
    assert "addItem" in javascript
    assert "updateItem" in javascript
    assert "removeItem" in javascript
    assert "formatError" in javascript
    assert "SecondMarketAuthAPI.me" in app_js
    assert "role !== \"buyer\"" in app_js
    assert "refreshCart" in app_js
    assert "updateCartItemQuantity" in app_js
    assert "removeCartItem" in app_js
    assert "actionLoading" in app_js
    assert "/checkout/pages/${templateName}.html" in app_js
    assert "renderCartStatus" in app_js
    assert "renderCartPage" in cart_page_js
    assert "checkoutDisabled" in cart_page_js
    assert "checkoutApp.updateCartItemQuantity" in cart_page_js
    assert "checkoutApp.removeCartItem" in cart_page_js
    assert "data-checkout-action" in cart_page_js
    assert "renderSummaryPage" in summary_page_js
    assert "/orders?order=" in summary_page_js
    assert "View Order" in summary_page_js
