"""
SkyWalking Provider for Keep

This provider integrates with Apache SkyWalking APM to fetch metrics and alerts.
"""

import logging
from typing import Optional

import requests

from keep.contextmanager.contextmanager import ContextManager
from keep.providers.base.base_provider import BaseProvider
from keep.providers.models.provider_config import ProviderConfig, ProviderScope

logger = logging.getLogger(__name__)

class SkywalkingProvider(BaseProvider):
    """Fetch alerts and metrics from Apache SkyWalking."""

    PROVIDER_DISPLAY_NAME = "SkyWalking"
    PROVIDER_TAGS = ["alert", "metrics", "apm", "observability"]
    PROVIDER_DESCRIPTION = "Apache SkyWalking is an APM (Application Performance Monitoring) platform for distributed systems."

    PROVIDER_SCOPES = [
        ProviderScope(
            name="authenticated",
            description="Authenticated to SkyWalking API",
            mandatory=True,
            alias="Authentication",
        ),
    ]

    def __init__(
        self,
        context_manager: ContextManager,
        provider_id: str,
        config: ProviderConfig,
    ):
        super().__init__(context_manager, provider_id, config)

    def dispose(self):
        """Dispose the provider."""
        pass

    def validate_config(self):
        """Validate provider configuration."""
        self.authentication_config.validate("skywalking_url")
        self.authentication_config.validate("authentication_token")
        pass

    def validate_scopes(self):
        """Validate provider scopes."""
        try:
            response = requests.get(
                f"{self.authentication_config.skywalking_url}/graphql",
                headers={"Authorization": f"Bearer {self.authentication_config.authentication_token}"},
                timeout=10,
            )
            if response.status_code == 200:
                return {
                    "authenticated": True,
                }
            else:
                logger.error(f"Failed to authenticate: {response.status_code}")
                return {
                    "authenticated": False,
                }
        except Exception as e:
            logger.error(f"Failed to validate scopes: {e}")
            return {
                "authenticated": False,
            }

    def _get_alerts(self, limit: Optional[int] = None):
        """Fetch alerts from SkyWalking."""
        try:
            # Query SkyWalking API for alarms
            query = """
            query {
                alarm: queryAlarm {
                    message
                    startTime
                    scope
                    tags {
                        key
                        value
                    }
                }
            }
            """

            response = requests.post(
                f"{self.authentication_config.skywalking_url}/graphql",
                headers={
                    "Authorization": f"Bearer {self.authentication_config.authentication_token}",
                    "Content-Type": "application/json",
                },
                json={"query": query},
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                alarms = data.get("data", {}).get("alarm", [])

                alerts = []
                for alarm in alarms[:limit] if limit else alarms:
                    alerts.append({
                        "id": alarm.get("id", ""),
                        "message": alarm.get("message", ""),
                        "startedAt": alarm.get("startTime", ""),
                        "scope": alarm.get("scope", ""),
                        "tags": alarm.get("tags", []),
                    })

                return alerts
            else:
                logger.error(f"Failed to fetch alarms: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Failed to fetch alerts from SkyWalking: {e}")
            return []

    def _notify(self, **kwargs):
        """Notify SkyWalking (not implemented for this provider)."""
        raise NotImplementedError("_notify is not implemented for SkyWalking provider")
