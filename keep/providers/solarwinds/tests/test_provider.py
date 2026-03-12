
"""
Tests for SolarWinds Provider
"""

import pytest
from keep.providers.providers_factory import ProvidersFactory

def test_validate_config():
    """Test provider configuration validation."""
    config = {
        "authentication": {
            "solarwinds_url": "https://solarwinds.example.com",
            "username": "admin",
            "password": "password",
        }
    }

    provider = ProvidersFactory.get_provider(
        provider_id="solarwinds-test",
        provider_type="solarwinds",
        config=config,
    )

    assert provider is not None

def test_get_alerts_mock(mocker):
    """Test fetching alerts from SolarWinds."""
    config = {
        "authentication": {
            "solarwinds_url": "https://solarwinds.example.com",
            "username": "admin",
            "password": "password",
        }
    }

    provider = ProvidersFactory.get_provider(
        provider_id="solarwinds-test",
        provider_type="solarwinds",
        config=config,
    )

    # Mock the HTTP request
    mock_response = {
        "results": [
            {
                "AlertID": "1",
                "AlertName": "High CPU",
                "AlertMessage": "CPU usage is above 90%",
                "TriggeredDateTime": "2026-03-12T00:00:00Z",
                "Severity": "Critical",
                "ObjectName": "Server-01",
                "NodeID": "123",
            }
        ]
    }

    mocker.patch("requests.post", return_value=mocker.MagicMock(
        status_code=200,
        json=lambda: mock_response
    ))

    alerts = provider._get_alerts(limit=10)

    assert len(alerts) == 1
    assert alerts[0]["name"] == "High CPU"
