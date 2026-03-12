"""
SplunkProvider is a class that provides a way to interact with Splunk.
Splunk log analytics
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
class SplunkProviderAuthConfig:
    api_key: str = dataclasses.field(
        metadata={
            "description": "Splunk API key",
            "sensitive": True,
            "required": True,
        }
    )
    url: pydantic.AnyHttpUrl = dataclasses.field(
        metadata={
            "description": "Splunk server URL (optional)",
            "hint": "https://splunk.example.com",
            "validation": "any_http_url",
        },
        default=None,
    )


class SplunkProvider(BaseProvider, ProviderHealthMixin):
    """Get alerts from Splunk into Keep."""

    PROVIDER_CATEGORY = ["logging"]
    PROVIDER_DISPLAY_NAME = "Splunk"
    
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
        self.logger.info("Validating Splunk provider config")
        pass
    
    def _get_alerts(self):
        """Get alerts from Splunk."""
        try:
            auth_config = SplunkProviderAuthConfig(**self.authentication_config)
            
            # TODO: Implement actual API call to Splunk
            # This is a template that needs to be filled with Splunk-specific API calls
            
            self.logger.info("Fetching alerts from Splunk")
            
            # Placeholder for API implementation
            # response = requests.get(...)
            # alerts = []
            # for item in response.json():
            #     alert = AlertDto(...)
            #     alerts.append(alert)
            # return alerts
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error fetching Splunk alerts: {e}")
            return []

if __name__ == "__main__":
    print("Splunk Provider loaded successfully")
