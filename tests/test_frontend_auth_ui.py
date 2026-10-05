from backend.app import create_app
from backend.app.core.config import TestingConfig


def test_storefront_references_auth_frontend_assets():
    app = create_app(TestingConfig)

    response = app.test_client().get("/")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "/static/css/auth.css" in html
    assert "/static/js/auth-client.js" in html
    assert "/static/js/auth-views.js" in html
    assert "/static/js/marketplace/app.js" in html
    assert "window.location.href='/login.html'" in html
    assert "window.location.href='/admin/login.html'" not in html

    app_js = app.test_client().get("/static/js/marketplace/app.js").get_data(as_text=True)
    assert "SecondMarketAuthViews.renderAuthView" in app_js


def test_auth_frontend_assets_are_served():
    app = create_app(TestingConfig)
    client = app.test_client()

    css_response = client.get("/static/css/auth.css")
    js_response = client.get("/static/js/auth-client.js")
    page_js_response = client.get("/static/js/auth-page.js")
    views_response = client.get("/static/js/auth-views.js")

    assert css_response.status_code == 200
    assert ".auth-shell" in css_response.get_data(as_text=True)
    assert js_response.status_code == 200
    assert "SecondMarketAuthAPI" in js_response.get_data(as_text=True)
    assert page_js_response.status_code == 200
    assert "data-auth-form" in page_js_response.get_data(as_text=True)
    assert "redirectAuthenticatedUser" in page_js_response.get_data(as_text=True)
    assert "authRequiredRole" in page_js_response.get_data(as_text=True)
    assert views_response.status_code == 200
    assert "renderAuthView" in views_response.get_data(as_text=True)
    assert "/register.html" in views_response.get_data(as_text=True)
    assert 'window.location.href = "/admin"' in views_response.get_data(as_text=True)


def test_login_and_register_pages_are_served_as_separate_files():
    app = create_app(TestingConfig)
    client = app.test_client()

    login_response = client.get("/login.html")
    admin_login_response = client.get("/admin/login.html")
    register_response = client.get("/register.html")

    assert login_response.status_code == 200
    assert 'data-auth-form="login"' in login_response.get_data(as_text=True)
    assert 'data-auth-required-role="buyer"' in login_response.get_data(as_text=True)
    assert "/admin/login.html" in login_response.get_data(as_text=True)
    assert "/static/js/auth-page.js" in login_response.get_data(as_text=True)
    assert admin_login_response.status_code == 200
    assert "Admin Seller Sign In" in admin_login_response.get_data(as_text=True)
    assert 'data-auth-required-role="admin"' in admin_login_response.get_data(as_text=True)
    assert 'data-auth-success-url="/admin"' in admin_login_response.get_data(as_text=True)
    assert "/static/js/auth-page.js" in admin_login_response.get_data(as_text=True)
    assert register_response.status_code == 200
    assert 'data-auth-form="register"' in register_response.get_data(as_text=True)
    assert "/static/js/auth-page.js" in register_response.get_data(as_text=True)
