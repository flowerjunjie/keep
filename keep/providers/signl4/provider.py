"""
SIGNL4 Provider for Keep

This provider sends alerts to SIGNL4, a critical alert management platform.
"""

import logging
from typing import Optional
import json
import requests

from keep.contextmanager.contextmanager import ContextManager
from keep.providers.base.base_provider import BaseProvider
from keep.providers.models.provider_config import ProviderConfig, ProviderScope

logger = logging.getLogger(__name__)

class Signl4Provider(BaseProvider):
    """Send alerts to SIGNL4 for critical alert management."""

    PROVIDER_DISPLAY_NAME = "SIGNL4"
    PROVIDER_TAGS = ["alert", "critical", "incident", "scheduling", "mobile"]
    PROVIDER_DESCRIPTION = "SIGNL4 provider for sending critical alerts to mobile teams with intelligent alert escalation and scheduling."

    PROVIDER_SCOPES = [
        ProviderScope(
            name="authenticated",
            description="SIGNL4 webhook URL is configured",
            mandatory=True,
            alias="Configuration",
        ),
    ]

    def __init__(
        self,
        context_manager: ContextManager,
        provider_id: str,
        config: ProviderConfig,
    ):
        super().__init__(context_manager, provider_id, config)
        self.webhook_url = None

    def dispose(self):
        """Dispose the provider."""
        pass

    def validate_config(self):
        """Validate provider configuration."""
        self.authentication_config.validate("webhook_url")
        self.webhook_url = self.authentication_config.get("webhook_url")

    def validate_scopes(self):
        """Validate provider scopes."""
        try:
            # Test webhook URL accessibility
            response = requests.options(
                self.webhook_url,
                timeout=10,
                headers={"Content-Type": "application/json"}
            )
            return True
        except Exception as e:
            logger.error(f"SIGNL4 webhook validation failed: {e}")
            return False

    def _notify(
        self,
        title: str,
        message: str,
        severity: str = "high",
        host: Optional[str] = None,
        service: Optional[str] = None,
        status: Optional[str] = "firing",
        **kwargs
    ):
        """
        Send alert to SIGNL4.

        Args:
            title: Alert title
            message: Alert message/description
            severity: Alert severity (low, medium, high, critical)
            host: Host where the alert originated
            service: Service related to the alert
            status: Alert status (firing, resolved)
            **kwargs: Additional alert fields
        """
        # Build SIGNL4 alert payload
        alert_payload = {
            "title": title,
            "body": message,
            "severity": severity,
            "status": status,
        }

        # Add optional fields
        if host:
            alert_payload["host"] = host
        if service:
            alert_payload["service"] = service

        # Add any additional fields
        alert_payload.update(kwargs)

        try:
            response = requests.post(
                self.webhook_url,
                json=alert_payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            logger.info(f"SIGNL4 alert sent successfully: {title}")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to send SIGNL4 alert: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise

    def notify(
        self,
        title: str,
        message: str,
        severity: str = "high",
        host: Optional[str] = None,
        service: Optional[str] = None,
        status: Optional[str] = "firing",
        **kwargs
    ):
        """
        Send alert notification to SIGNL4.

        Args:
            title: Alert title
            message: Alert message
            severity: Alert severity level
            host: Source host
            service: Affected service
            status: Alert status
            **kwargs: Additional parameters
        """
        return self._notify(
            title=title,
            message=message,
            severity=severity,
            host=host,
            service=service,
            status=status,
            **kwargs
        )

    def query(self, **kwargs):
        """Query is not supported for SIGNL4 provider."""
        raise NotImplementedError("Query operation is not supported for SIGNL4 provider")
