import os
import pytest
from keep.providers.pushover.provider import PushoverProvider
from keep.providers.models.provider_config import ProviderConfig

# Mock credentials for testing
TEST_API_TOKEN = "test_api_token"
TEST_USER_KEY = "test_user_key"

@pytest.fixture
def pushover_config():
    """Create test Pushover provider configuration."""
    return ProviderConfig(
        authentication={
            "api_token": TEST_API_TOKEN,
            "user_key": TEST_USER_KEY
        },
        description="Test Pushover provider"
    )

@pytest.fixture
def pushover_provider(pushover_config):
    """Create Pushover provider instance."""
    return PushoverProvider(
        context_manager=None,
        provider_id="test-pushover",
        config=pushover_config
    )

def test_provider_initialization(pushover_provider):
    """Test provider initialization."""
    assert pushover_provider.PROVIDER_DISPLAY_NAME == "Pushover"
    assert "alert" in pushover_provider.PROVIDER_TAGS
    assert "mobile" in pushover_provider.PROVIDER_TAGS
    assert pushover_provider.api_token == TEST_API_TOKEN
    assert pushover_provider.user_key == TEST_USER_KEY

def test_provider_scopes(pushover_provider):
    """Test provider scopes."""
    scopes = pushover_provider.PROVIDER_SCOPES
    assert len(scopes) > 0
    assert scopes[0].name == "authenticated"
    assert scopes[0].mandatory == True

def test_provider_dispose(pushover_provider):
    """Test provider disposal."""
    pushover_provider.dispose()
    # Should not raise any exceptions
    assert True

def test_validate_config(pushover_config):
    """Test configuration validation."""
    provider = PushoverProvider(
        context_manager=None,
        provider_id="test-pushover",
        config=pushover_config
    )
    assert provider.api_token == TEST_API_TOKEN
    assert provider.user_key == TEST_USER_KEY

def test_validate_config_missing_credentials():
    """Test configuration validation with missing credentials."""
    config = ProviderConfig(
        authentication={},
        description="Test Pushover provider"
    )
    provider = PushoverProvider(
        context_manager=None,
        provider_id="test-pushover",
        config=config
    )
    with pytest.raises(Exception):
        provider.validate_config()
