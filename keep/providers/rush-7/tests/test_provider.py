
"""
Tests for SNMP Provider
"""

import pytest
from keep.providers.providers_factory import ProvidersFactory

def test_validate_config():
    """Test provider configuration validation."""
    config = {
        "authentication": {
            "host": "0.0.0.0",
            "port": "162",
        }
    }

    provider = ProvidersFactory.get_provider(
        provider_id="snmp-test",
        provider_type="snmp",
        config=config,
    )

    assert provider is not None

def test_severity_mapping():
    """Test SNMP severity mapping."""
    config = {
        "authentication": {
            "host": "0.0.0.0",
            "port": "162",
        }
    }

    provider = ProvidersFactory.get_provider(
        provider_id="snmp-test",
        provider_type="snmp",
        config=config,
    )

    assert provider._map_severity("emergency") == "critical"
    assert provider._map_severity("warning") == "warning"
    assert provider._map_severity("debug") == "info"

def test_parse_snmp_trap():
    """Test SNMP trap parsing."""
    config = {
        "authentication": {
            "host": "0.0.0.0",
            "port": "162",
        }
    }

    provider = ProvidersFactory.get_provider(
        provider_id="snmp-test",
        provider_type="snmp",
        config=config,
    )

    raw_trap = b"test_trap_data"
    parsed = provider.parse_snmp_trap(raw_trap)

    assert "raw_data" in parsed
    assert parsed["raw_data"] == "746573745f747261705f64617461"
