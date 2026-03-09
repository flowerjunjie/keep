"""
SensuProvider is a class that provides a set of methods to interact with the Sensu API.
"""

import dataclasses
import datetime
import requests

import pydantic

from keep.api.models.alert import AlertDto, AlertSeverity, AlertStatus
from keep.contextmanager.contextmanager import ContextManager
from keep.exceptions.provider_exception import ProviderException
from keep.providers.base.base_provider import BaseProvider
from keep.providers.models.provider_config import ProviderConfig, ProviderScope


@pydantic.dataclasses.dataclass
class SensuProviderAuthConfig:
    """
    SensuProviderAuthConfig is a class that holds the authentication information for the SensuProvider.
    """

    host_url: pydantic.AnyHttpUrl = dataclasses.field(
        metadata={
            "required": True,
            "description": "Sensu Host URL (e.g., https://sensu.example.com)",
            "sensitive": False,
            "validation": "any_http_url",
        },
    )

    api_token: str = dataclasses.field(
        metadata={
            "required": True,
            "description": "Sensu API Token",
            "sensitive": True,
        },
        default=None,
    )

    verify_ssl: bool = dataclasses.field(
        metadata={
            "required": False,
            "description": "Verify SSL certificate",
            "sensitive": False,
        },
        default=True,
    )


class SensuProvider(BaseProvider):
    PROVIDER_DISPLAY_NAME = "Sensu"
    PROVIDER_TAGS = ["alert", "monitoring"]
    PROVIDER_CATEGORY = ["Monitoring"]
    PROVIDER_SCOPES = [
        ProviderScope(name="authenticated", description="User is authenticated"),
    ]

    """
    Sensu monitoring states mapping
    """

    STATUS_MAP = {
        "firing": AlertStatus.FIRING,
        "resolved": AlertStatus.RESOLVED,
        "pending": AlertStatus.PENDING,
    }

    SEVERITY_MAP = {
        "critical": AlertSeverity.CRITICAL,
        "warning": AlertSeverity.WARNING,
        "info": AlertSeverity.INFO,
        "ok": AlertSeverity.LOW,
    }

    def __init__(
        self, context_manager: ContextManager, provider_id: str, config: ProviderConfig
    ):
        super().__init__(context_manager, provider_id, config)

    def dispose(self):
        pass

    def validate_config(self):
        """
        Validates the configuration of the Sensu provider.
        """
        self.logger.info("Validating Sensu provider configuration")

        try:
            # Test authentication by fetching Sensu events
            response = self._query_sensu("events")

            if response.status_code == 200:
                self.logger.info("Sensu provider configuration is valid")
                return {"authenticated": True}
            else:
                raise ProviderException(
                    f"Failed to authenticate with Sensu: {response.status_code}"
                )
        except Exception as e:
            self.logger.error(f"Failed to validate Sensu configuration: {e}")
            raise ProviderException(f"Failed to validate Sensu configuration: {e}")

    def _query_sensu(self, endpoint: str, method: str = "GET", data: dict = None):
        """
        Query the Sensu API.
        """
        config = self.config.authentication

        url = f"{config.host_url.rstrip('/')}/api/core/v2/{endpoint}"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.api_token}",
        }

        params = {
            "verify_ssl": config.verify_ssl if hasattr(config, 'verify_ssl') else True
        }

        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, params=params)
            else:
                raise ProviderException(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            raise ProviderException(f"Failed to query Sensu API: {e}")

    def _get_alerts(self) -> list[AlertDto]:
        """
        Get alerts from Sensu.
        """
        self.logger.info("Getting alerts from Sensu")

        try:
            # Query events (alerts in Sensu)
            response = self._query_sensu("namespaces/default/events")

            alerts = []

            if response.status_code == 200:
                data = response.json()
                for event in data.get("items", []):
                    alert = self._parse_event(event)
                    if alert:
                        alerts.append(alert)

            self.logger.info(f"Retrieved {len(alerts)} alerts from Sensu")
            return alerts

        except Exception as e:
            self.logger.error(f"Failed to get alerts from Sensu: {e}")
            raise ProviderException(f"Failed to get alerts from Sensu: {e}")

    def _parse_event(self, event: dict) -> AlertDto:
        """
        Parse a Sensu event into an AlertDto.
        """
        # Extract check information
        check = event.get("check", {})
        entity = event.get("entity", {})

        # Determine status and severity
        check_state = check.get("state", "passing")
        status = AlertStatus.FIRING if check_state != "passing" else AlertStatus.RESOLVED

        severity = AlertSeverity.INFO
        if check_state == "critical":
            severity = AlertSeverity.CRITICAL
        elif check_state == "warning":
            severity = AlertSeverity.WARNING
        elif check_state == "passing":
            severity = AlertSeverity.LOW

        return AlertDto(
            id=f"sensu-{event.get('id', 'unknown')}",
            name=f"{entity.get('metadata', {}).get('name', 'Unknown')}: {check.get('metadata', {}).get('name', 'Unknown')}",
            status=status,
            severity=severity,
            lastReceived=datetime.datetime.now().isoformat(),
            description=check.get("output", "No output available"),
            source=["sensu"],
            labels={
                "check": check.get("metadata", {}).get("name", "unknown"),
                "entity": entity.get("metadata", {}).get("name", "unknown"),
                "state": check_state,
            },
        )

    def get_alerts(self) -> list[AlertDto]:
        """
        Get alerts from Sensu.
        """
        return self._get_alerts()

    def notify(self, alert: AlertDto | dict = None):
        """
        Notify Sensu about an alert (not implemented).
        """
        raise ProviderException("Sensu provider does not support sending alerts")

    def setup_webhook(
        self, tenant_id: str, keep_api_url: str, api_key: str, setup_alerts: bool = True
    ):
        """
        Setup webhook for Sensu (not applicable).
        """
        raise ProviderException("Webhooks are not supported for Sensu provider")
