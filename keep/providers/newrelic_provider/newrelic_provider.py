"""
NewRelicProvider is a class that provides a way to interact with NewRelic.
NewRelic APM
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
class NewRelicProviderAuthConfig:
    api_key: str = dataclasses.field(
        metadata={
            "description": "NewRelic API key",
            "sensitive": True,
            "required": True,
        }
    )
    url: pydantic.AnyHttpUrl = dataclasses.field(
        metadata={
            "description": "NewRelic server URL (optional)",
            "hint": "https://newrelic.example.com",
            "validation": "any_http_url",
        },
        default=None,
    )


class NewRelicProvider(BaseProvider, ProviderHealthMixin):
    """Get alerts from NewRelic into Keep."""

    PROVIDER_CATEGORY = ["monitoring"]
    PROVIDER_DISPLAY_NAME = "NewRelic"
    
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
        self.logger.info("Validating NewRelic provider config")
        pass
    
    def _get_alerts(self):
        """Get alerts from NewRelic."""
        try:
            auth_config = NewRelicProviderAuthConfig(**self.authentication_config)
            
            # TODO: Implement actual API call to NewRelic
            # This is a template that needs to be filled with NewRelic-specific API calls
            
            self.logger.info("Fetching alerts from NewRelic")
            
            # Placeholder for API implementation
            # response = requests.get(...)
            # alerts = []
            # for item in response.json():
            #     alert = AlertDto(...)
            #     alerts.append(alert)
            # return alerts
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error fetching NewRelic alerts: {e}")
            return []

if __name__ == "__main__":
    print("NewRelic Provider loaded successfully")
