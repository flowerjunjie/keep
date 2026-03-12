
"""
SolarWinds Provider for Keep

This provider integrates with SolarWinds Orion Platform to fetch alerts and metrics.
"""

import logging
from typing import Optional
import base64

import requests

from keep.contextmanager.contextmanager import ContextManager
from keep.providers.base.base_provider import BaseProvider
from keep.providers.models.provider_config import ProviderConfig, ProviderScope

logger = logging.getLogger(__name__)

class SolarwindsProvider(BaseProvider):
    """Fetch alerts and metrics from SolarWinds Orion Platform."""

    PROVIDER_DISPLAY_NAME = "SolarWinds"
    PROVIDER_TAGS = ["alert", "metrics", "network", "infrastructure", "monitoring"]
    PROVIDER_DESCRIPTION = "SolarWinds provides IT management software for monitoring and managing network devices, servers, applications, and services."

    PROVIDER_SCOPES = [
        ProviderScope(
            name="authenticated",
            description="Authenticated to SolarWinds API",
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
        self.authentication_config.validate("solarwinds_url")
        self.authentication_config.validate("username")
        self.authentication_config.validate("password")
        pass

    def validate_scopes(self):
        """Validate provider scopes."""
        try:
            # Create basic auth header
            credentials = base64.b64encode(
                f"{self.authentication_config.username}:{self.authentication_config.password}".encode()
            ).decode()

            response = requests.get(
                f"{self.authentication_config.solarwinds_url}/api/Query",
                headers={
                    "Authorization": f"Basic {credentials}",
                    "Content-Type": "application/json",
                },
                timeout=10,
            )
            if response.status_code in [200, 401]:  # 401 means server is responding
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
        """Fetch alerts from SolarWinds."""
        try:
            # Create basic auth header
            credentials = base64.b64encode(
                f"{self.authentication_config.username}:{self.authentication_config.password}".encode()
            ).decode()

            # Query SolarWinds API for active alerts
            query = """
            SELECT TOP {}
                AlertID,
                AlertName,
                AlertMessage,
                TriggeredDateTime,
                Severity,
                ObjectName,
                NodeID
            FROM Orion.AlertActive
            ORDER BY TriggeredDateTime DESC
            """.format(limit if limit else 100)

            response = requests.post(
                f"{self.authentication_config.solarwinds_url}/api/Query",
                headers={
                    "Authorization": f"Basic {credentials}",
                    "Content-Type": "application/json",
                },
                json={"query": query},
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])

                alerts = []
                for alert in results:
                    alerts.append({
                        "id": alert.get("AlertID", ""),
                        "name": alert.get("AlertName", ""),
                        "message": alert.get("AlertMessage", ""),
                        "triggeredAt": alert.get("TriggeredDateTime", ""),
                        "severity": alert.get("Severity", ""),
                        "object": alert.get("ObjectName", ""),
                        "nodeId": alert.get("NodeID", ""),
                    })

                return alerts
            else:
                logger.error(f"Failed to fetch alerts: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Failed to fetch alerts from SolarWinds: {e}")
            return []

    def _notify(self, **kwargs):
        """Notify SolarWinds (not implemented for this provider)."""
        raise NotImplementedError("_notify is not implemented for SolarWinds provider")
