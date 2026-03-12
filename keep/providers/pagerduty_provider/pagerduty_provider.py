"""
PagerDutyProvider is a class that provides a way to interact with PagerDuty.
PagerDuty incident response
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
class PagerDutyProviderAuthConfig:
    api_key: str = dataclasses.field(
        metadata={
            "description": "PagerDuty API key",
            "sensitive": True,
            "required": True,
        }
    )
    url: pydantic.AnyHttpUrl = dataclasses.field(
        metadata={
            "description": "PagerDuty server URL (optional)",
            "hint": "https://pagerduty.example.com",
            "validation": "any_http_url",
        },
        default=None,
    )


class PagerDutyProvider(BaseProvider, ProviderHealthMixin):
    """Get alerts from PagerDuty into Keep."""

    PROVIDER_CATEGORY = ["incident_management"]
    PROVIDER_DISPLAY_NAME = "PagerDuty"
    
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
        self.logger.info("Validating PagerDuty provider config")
        pass
    
    def _get_alerts(self):
        """Get alerts from PagerDuty."""
        try:
            auth_config = PagerDutyProviderAuthConfig(**self.authentication_config)
            
            # TODO: Implement actual API call to PagerDuty
            # This is a template that needs to be filled with PagerDuty-specific API calls
            
            self.logger.info("Fetching alerts from PagerDuty")
            
            # Placeholder for API implementation
            # response = requests.get(...)
            # alerts = []
            # for item in response.json():
            #     alert = AlertDto(...)
            #     alerts.append(alert)
            # return alerts
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error fetching PagerDuty alerts: {e}")
            return []

if __name__ == "__main__":
    print("PagerDuty Provider loaded successfully")
