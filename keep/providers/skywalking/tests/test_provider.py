"""
Tests for SkyWalking Provider
"""

import pytest
from keep.providers.providers_factory import ProvidersFactory

def test_validate_config():
    """Test provider configuration validation."""
    config = {
        "authentication": {
            "skywalking_url": "http://localhost:8080",
            "authentication_token": "test_token",
        }
    }

    provider = ProvidersFactory.get_provider(
        provider_id="skywalking-test",
        provider_type="skywalking",
        config=config,
    )

    assert provider is not None

def test_get_alerts_mock(mocker):
    """Test fetching alerts from SkyWalking."""
    config = {
        "authentication": {
            "skywalking_url": "http://localhost:8080",
            "authentication_token": "test_token",
        }
    }

    provider = ProvidersFactory.get_provider(
        provider_id="skywalking-test",
        provider_type="skywalking",
        config=config,
    )

    # Mock the HTTP request
    mock_response = {
        "data": {
            "alarm": [
                {
                    "id": "1",
                    "message": "High CPU usage",
                    "startTime": "2026-03-12T00:00:00Z",
                    "scope": "SERVICE",
                    "tags": [{"key": "service", "value": "my-service"}],
                }
            ]
        }
    }

    mocker.patch("requests.post", return_value=mocker.MagicMock(
        status_code=200,
        json=lambda: mock_response
    ))

    alerts = provider._get_alerts(limit=10)

    assert len(alerts) == 1
    assert alerts[0]["message"] == "High CPU usage"
