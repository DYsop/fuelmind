from __future__ import annotations

from app.core.config import get_settings


def test_health_endpoint_reports_service_state(configured_app):
    _, client = configured_app
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["database"] == "ok"
    assert payload["external_api_configured"] is False


def test_configuration_works_without_api_key(configured_app):
    settings = get_settings()
    assert settings.external_api_configured is False
    assert settings.allow_public_api is True

