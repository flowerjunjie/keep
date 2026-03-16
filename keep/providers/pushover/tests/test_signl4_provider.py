import os
import pytest
from keep.providers.signl4.provider import Signl4Provider
from keep.providers.models.provider_config import ProviderConfig

# Mock webhook URL for testing
TEST_WEBHOOK_URL = "https://connect.signl4.com/webhook/test"

@pytest.fixture
def signl4_config():
    """Create test SIGNL4 provider configuration."""
    return ProviderConfig(
        authentication={
            "webhook_url": TEST_WEBHOOK_URL
        },
        description="Test SIGNL4 provider"
    )

@pytest.fixture
def signl4_provider(signl4_config):
    """Create SIGNL4 provider instance."""
    return Signl4Provider(
        context_manager=None,
        provider_id="test-signl4",
        config=signl4_config
    )

def test_provider_initialization(signl4_provider):
    """Test provider initialization."""
    assert signl4_provider.PROVIDER_DISPLAY_NAME == "SIGNL4"
    assert "alert" in signl4_provider.PROVIDER_TAGS
    assert "critical" in signl4_provider.PROVIDER_TAGS
    assert signl4_provider.webhook_url == TEST_WEBHOOK_URL

def test_provider_scopes(signl4_provider):
    """Test provider scopes."""
    scopes = signl4_provider.PROVIDER_SCOPES
    assert len(scopes) > 0
    assert scopes[0].name == "authenticated"
    assert scopes[0].mandatory == True

def test_provider_dispose(signl4_provider):
    """Test provider disposal."""
    signl4_provider.dispose()
    # Should not raise any exceptions
    assert True

def test_validate_config(signl4_config):
    """Test configuration validation."""
    provider = Signl4Provider(
        context_manager=None,
        provider_id="test-signl4",
        config=signl4_config
    )
    assert provider.webhook_url == TEST_WEBHOOK_URL

def test_validate_config_missing_webhook():
    """Test configuration validation with missing webhook URL."""
    config = ProviderConfig(
        authentication={},
        description="Test SIGNL4 provider"
    )
    provider = Signl4Provider(
        context_manager=None,
        provider_id="test-signl4",
        config=config
    )
    with pytest.raises(Exception):
        provider.validate_config()
