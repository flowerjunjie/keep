"""
TelegramProvider is a class that provides a way to interact with Telegram.
Telegram bot alerts
"""

import dataclasses
import datetime
import os

import pydantic
import requests

from keep.api.models.alert import AlertDto, AlertSeverity, AlertStatus
from keep.contextmanager.contextmanager import ContextManager
from keep.providers.base.base_provider import BaseProvider, ProviderHealthMixin
from keep.providers.models.provider_config import ProviderConfig, ProviderScope


@pydantic.dataclasses.dataclass
class TelegramProviderAuthConfig:
    api_key: str = dataclasses.field(
        metadata={
            "description": "Telegram API key",
            "sensitive": True,
            "required": True,
        }
    )
    url: pydantic.AnyHttpUrl = dataclasses.field(
        metadata={
            "description": "Telegram server URL (optional)",
            "hint": "https://telegram.example.com",
            "validation": "any_http_url",
        },
        default=None,
    )


class TelegramProvider(BaseProvider, ProviderHealthMixin):
    """Get alerts from Telegram into Keep."""

    PROVIDER_CATEGORY = ["messaging"]
    PROVIDER_DISPLAY_NAME = "Telegram"
    
    SEVERITIES_MAP = {
        "critical": AlertSeverity.CRITICAL,
        "high": AlertSeverity.HIGH,
        "warning": AlertSeverity.WARNING,
        "info": AlertSeverity.INFO,
        "low": AlertSeverity.LOW,
    }

    STATUS_MAP = {
        "firing": AlertStatus.FIRING,
        "open": AlertStatus.FIRING,
        "resolved": AlertStatus.RESOLVED,
        "closed": AlertStatus.RESOLVED,
    }

    PROVIDER_SCOPES = [
        ProviderScope(
            name="connectivity",
            description="Connectivity Test",
            mandatory=True
        )
    ]

    def __init__(
        self, context_manager: ContextManager, provider_id: str, config: ProviderConfig
    ):
        super().__init__(context_manager, provider_id, config)
    
    def dispose(self):
        """Dispose the provider."""
        pass
    
    def validate_config(self):
        """Validate the provider configuration."""
        self.logger.info("Validating Telegram provider config")
        pass
    
    def _get_alerts(self):
        """Get alerts from Telegram."""
        try:
            auth_config = TelegramProviderAuthConfig(**self.authentication_config)
            
            # TODO: Implement actual API call to Telegram
            self.logger.info("Fetching alerts from Telegram")
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error fetching Telegram alerts: {e}")
            return []

if __name__ == "__main__":
    print("Telegram Provider loaded successfully")
