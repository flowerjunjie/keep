"""
SendgridProvider is a class that provides a way to interact with Sendgrid.
Sendgrid email service
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
class SendgridProviderAuthConfig:
    api_key: str = dataclasses.field(
        metadata={
            "description": "Sendgrid API key",
            "sensitive": True,
            "required": True,
        }
    )
    url: pydantic.AnyHttpUrl = dataclasses.field(
        metadata={
            "description": "Sendgrid server URL (optional)",
            "hint": "https://sendgrid.example.com",
            "validation": "any_http_url",
        },
        default=None,
    )


class SendgridProvider(BaseProvider, ProviderHealthMixin):
    """Get alerts from Sendgrid into Keep."""

    PROVIDER_CATEGORY = ["email"]
    PROVIDER_DISPLAY_NAME = "Sendgrid"
    
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
        self.logger.info("Validating Sendgrid provider config")
        pass
    
    def _get_alerts(self):
        """Get alerts from Sendgrid."""
        try:
            auth_config = SendgridProviderAuthConfig(**self.authentication_config)
            
            # TODO: Implement actual API call to Sendgrid
            self.logger.info("Fetching alerts from Sendgrid")
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error fetching Sendgrid alerts: {e}")
            return []

if __name__ == "__main__":
    print("Sendgrid Provider loaded successfully")
