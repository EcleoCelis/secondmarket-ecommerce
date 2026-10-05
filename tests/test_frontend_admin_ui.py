from backend.app import create_app
from backend.app.core.config import TestingConfig


def test_admin_frontend_shell_is_served_separately():
    app = create_app(TestingConfig)

    response = app.test_client().get("/admin")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Admin Seller | SecondMarket" in html
    assert "/static/css/admin/base.css" in html
    assert "/static/js/auth-client.js" in html
    assert "/static/js/admin/admin-api.js" in html
    assert "/static/js/admin/app.js" in html
    assert "/static/js/admin/pages/dashboard-page.js" in html
    assert "/static/js/admin/pages/products-page.js" in html
    assert "/static/js/admin/pages/categories-page.js" in html
    assert "/static/js/admin/pages/orders-page.js" in html
    assert 'data-admin-nav="orders"' in html
    assert "admin-main-content" in html
    assert "frontend/static/js/marketplace" not in html

    admin_login = app.test_client().get("/admin/login.html")
    assert admin_login.status_code == 200
    assert "Admin Seller Sign In" in admin_login.get_data(as_text=True)
    assert 'data-auth-required-role="admin"' in admin_login.get_data(as_text=True)


def test_admin_frontend_assets_are_served_separately():
    app = create_app(TestingConfig)
    client = app.test_client()

    expected_assets = {
        "/static/css/admin/base.css": ".admin-layout",
        "/static/js/admin/admin-api.js": "SecondMarketAdminAPI",
        "/static/js/admin/app.js": "class SecondMarketAdminApp",
        "/static/js/admin/pages/dashboard-page.js": "renderDashboardPage",
        "/static/js/admin/pages/products-page.js": "renderProductsPage",
        "/static/js/admin/pages/categories-page.js": "renderCategoriesPage",
        "/static/js/admin/pages/orders-page.js": "renderOrdersPage",
    }

    for asset_path, expected_text in expected_assets.items():
        response = client.get(asset_path)
        assert response.status_code == 200
        assert expected_text in response.get_data(as_text=True)

    css = client.get("/static/css/admin/base.css").get_data(as_text=True)
    assert ".admin-inline-actions" in css
    assert ".admin-quantity-action" in css
    assert ".admin-order-detail" in css
    assert ".admin-orders-table" in css
    assert "input:disabled" in css
    assert "select:disabled" in css


def test_admin_page_templates_are_served_separately():
    app = create_app(TestingConfig)
    client = app.test_client()

    expected_templates = {
        "/admin/pages/dashboard.html": "{{metricCards}}",
        "/admin/pages/products.html": "{{productRows}}",
        "/admin/pages/categories.html": "{{categoryRows}}",
        "/admin/pages/orders.html": "{{orderRows}}",
    }

    for template_path, expected_text in expected_templates.items():
        response = client.get(template_path)
        assert response.status_code == 200
        assert expected_text in response.get_data(as_text=True)

    categories_template = client.get("/admin/pages/categories.html").get_data(as_text=True)
    assert "adminApp.createCategory(event)" in categories_template
    assert "admin-category-name" in categories_template
    assert "{{categoryActionDisabled}}" in categories_template

    products_template = client.get("/admin/pages/products.html").get_data(as_text=True)
    assert "Full product form will be added" in products_template
    assert "Create workflow arrives in Module 5 Step 3" not in products_template

    orders_template = client.get("/admin/pages/orders.html").get_data(as_text=True)
    assert "adminApp.applyOrderFilters(event)" in orders_template
    assert "{{orderDetail}}" in orders_template
    assert "{{shippingOptions}}" in orders_template


def test_admin_frontend_client_targets_admin_api_contract():
    app = create_app(TestingConfig)
    client = app.test_client()

    javascript = client.get("/static/js/admin/admin-api.js").get_data(as_text=True)
    app_js = client.get("/static/js/admin/app.js").get_data(as_text=True)
    products_page_js = client.get("/static/js/admin/pages/products-page.js").get_data(as_text=True)
    categories_page_js = client.get("/static/js/admin/pages/categories-page.js").get_data(as_text=True)
    orders_page_js = client.get("/static/js/admin/pages/orders-page.js").get_data(as_text=True)

    assert 'const BASE_URL = "/api/v1/admin"' in javascript
    assert "listCategories" in javascript
    assert "createCategory" in javascript
    assert "updateCategory" in javascript
    assert "updateCategoryStatus" in javascript
    assert "listProducts" in javascript
    assert "listOrders" in javascript
    assert "getOrder" in javascript
    assert "updateProductStatus" in javascript
    assert "updateProductInventory" in javascript
    assert '`/categories/${encodeURIComponent(categorySlug)}`' in javascript
    assert '`/categories/${encodeURIComponent(categorySlug)}/status`' in javascript
    assert '`/products/${encodeURIComponent(productSlug)}/status`' in javascript
    assert '`/products/${encodeURIComponent(productSlug)}/inventory`' in javascript
    assert "URLSearchParams" in javascript
    assert "`/products${buildQueryString(filters)}`" in javascript
    assert "`/orders${buildQueryString(filters)}`" in javascript
    assert "`/orders/${encodeURIComponent(orderNumber)}`" in javascript
    assert "createCategory(event)" in app_js
    assert "actionLoading" in app_js
    assert "setActionLoading" in app_js
    assert "actionDisabledAttribute" in app_js
    assert "parseNonNegativeInteger" in app_js
    assert "non-negative whole number" in app_js
    assert "setCategoryStatus" in app_js
    assert "setCategorySortOrder" in app_js
    assert "setProductStatus" in app_js
    assert "setProductQuantity" in app_js
    assert "orderFilters" in app_js
    assert "applyOrderFilters" in app_js
    assert "resetOrderFilters" in app_js
    assert "loadAdminOrder" in app_js
    assert "renderOrdersPage" in app_js
    assert "/admin/login.html" in app_js
    assert "adminApp.setCategoryStatus" in categories_page_js
    assert "adminApp.setCategorySortOrder" in categories_page_js
    assert "categoryActionDisabled" in categories_page_js
    assert "data-admin-action" in categories_page_js
    assert "adminApp.setProductStatus" in products_page_js
    assert "adminApp.setProductQuantity" in products_page_js
    assert "data-admin-action" in products_page_js
    assert "adminApp.loadAdminOrder" in orders_page_js
    assert "renderOrderDetail" in orders_page_js
    assert "buyer?.email" in orders_page_js
