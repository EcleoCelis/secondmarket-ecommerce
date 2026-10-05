from backend.app import create_app
from backend.app.core.config import TestingConfig


def test_storefront_serves_existing_index():
    app = create_app(TestingConfig)

    response = app.test_client().get("/")

    assert response.status_code == 200
    assert b"<!DOCTYPE html>" in response.data
    assert b"SecondMarket" in response.data


def test_health_endpoint_uses_success_envelope():
    app = create_app(TestingConfig)

    response = app.test_client().get("/api/v1/health")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["data"]["status"] == "ok"
    assert payload["data"]["service"] == "api"


def test_system_info_documents_current_module_and_roles():
    app = create_app(TestingConfig)

    response = app.test_client().get("/api/v1/system/info")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["data"]["app"] == "SecondMarket"
    assert payload["data"]["api_version"] == "v1"
    assert payload["data"]["roles"] == ["buyer", "admin"]
    assert payload["data"]["modules"]["current"] == "01-system-foundation"


def test_missing_api_route_uses_error_envelope():
    app = create_app(TestingConfig)

    response = app.test_client().get("/api/v1/missing")
    payload = response.get_json()

    assert response.status_code == 404
    assert payload["success"] is False
    assert payload["error"]["code"] == "not_found"
