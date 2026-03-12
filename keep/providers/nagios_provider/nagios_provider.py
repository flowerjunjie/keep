"""
NagiosProvider is a class that provides a way to read alerts from Nagios.
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
class NagiosProviderAuthConfig:
    url: pydantic.AnyHttpUrl = dataclasses.field(
        metadata={
            "required": True,
            "description": "Nagios server URL",
            "hint": "https://nagios.example.com",
            "validation": "any_http_url",
        }
    )
    api_token: str = dataclasses.field(
        metadata={
            "description": "Nagios API token",
            "sensitive": True,
            "required": True,
        }
    )
    verify: bool = dataclasses.field(
        metadata={
            "description": "Verify SSL certificates",
            "hint": "Set to false to allow self-signed certificates",
            "sensitive": False,
        },
        default=True,
    )


class NagiosProvider(BaseProvider, ProviderHealthMixin):
    """Get alerts from Nagios into Keep."""

    PROVIDER_CATEGORY = ["Incident Management"]
    PROVIDER_DISPLAY_NAME = "Nagios"
    
    SEVERITIES_MAP = {
        "critical": AlertSeverity.CRITICAL,
        "down": AlertSeverity.CRITICAL,
        "error": AlertSeverity.HIGH,
        "high": AlertSeverity.HIGH,
        "warning": AlertSeverity.WARNING,
        "medium": AlertSeverity.WARNING,
        "unknown": AlertSeverity.INFO,
        "up": AlertSeverity.INFO,
        "ok": AlertSeverity.LOW,
    }

    STATUS_MAP = {
        "critical": AlertStatus.FIRING,
        "down": AlertStatus.FIRING,
        "warning": AlertStatus.FIRING,
        "unknown": AlertStatus.FIRING,
        "ok": AlertStatus.RESOLVED,
        "up": AlertStatus.RESOLVED,
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
        self.logger.info("Validating Nagios provider config")
        pass
    
    def _get_alerts(self):
        """Get alerts from Nagios."""
        try:
            auth_config = NagiosProviderAuthConfig(**self.authentication_config)
            headers = {
                "Authorization": f"Bearer {auth_config.api_token}",
                "Accept": "application/json"
            }
            
            response = requests.get(
                f"{auth_config.url}/api/v1/objects/services",
                headers=headers,
                verify=auth_config.verify,
                timeout=10
            )
            
            if response.status_code != 200:
                self.logger.error(f"Failed to fetch alerts: {response.status_code}")
                return []
            
            data = response.json()
            alerts = []
            
            for service in data.get('services', []):
                alert = AlertDto(
                    title=f"Nagios Service Alert: {service.get('name', 'Unknown')}",
                    description=service.get('plugin_output', ''),
                    severity=self.SEVERITIES_MAP.get(
                        service.get('state', 'unknown').lower(),
                        AlertSeverity.INFO
                    ),
                    status=self.STATUS_MAP.get(
                        service.get('state', 'unknown').lower(),
                        AlertStatus.FIRING
                    ),
                    source="nagios",
                    url=f"{auth_config.url}/cgi-bin/nagios.cgi?type=services&host={service.get('host_name', '')}",
                    labels={
                        "host": service.get('host_name', ''),
                        "service": service.get('name', ''),
                        "state": service.get('state', ''),
                    },
                    lastReceived=datetime.datetime.now().isoformat(),
                )
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Error fetching Nagios alerts: {e}")
            return []

if __name__ == "__main__":
    # Output for testing
    import json
    print("Nagios Provider loaded successfully")
