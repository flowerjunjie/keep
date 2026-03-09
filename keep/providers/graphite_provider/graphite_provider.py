"""
GraphiteProvider is a class that provides a set of methods to interact with Graphite metrics.
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
class GraphiteProviderAuthConfig:
    """
    GraphiteProviderAuthConfig is a class that holds the authentication information for the GraphiteProvider.
    """

    host_url: pydantic.AnyHttpUrl = dataclasses.field(
        metadata={
            "required": True,
            "description": "Graphite Host URL (e.g., https://graphite.example.com)",
            "sensitive": False,
            "validation": "any_http_url",
        },
    )

    api_key: str = dataclasses.field(
        metadata={
            "required": False,
            "description": "Graphite API Key (if authentication is enabled)",
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


class GraphiteProvider(BaseProvider):
    PROVIDER_DISPLAY_NAME = "Graphite"
    PROVIDER_TAGS = ["alert", "monitoring", "metrics"]
    PROVIDER_CATEGORY = ["Monitoring", "Metrics"]
    PROVIDER_SCOPES = [
        ProviderScope(name="authenticated", description="User is authenticated"),
    ]

    """
    Graphite metric states mapping
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
        Validates the configuration of the Graphite provider.
        """
        self.logger.info("Validating Graphite provider configuration")

        try:
            # Test authentication by querying Graphite metrics
            response = self._query_graphite("metrics/find?query=*")

            if response.status_code == 200:
                self.logger.info("Graphite provider configuration is valid")
                return {"authenticated": True}
            else:
                raise ProviderException(
                    f"Failed to authenticate with Graphite: {response.status_code}"
                )
        except Exception as e:
            self.logger.error(f"Failed to validate Graphite configuration: {e}")
            raise ProviderException(f"Failed to validate Graphite configuration: {e}")

    def _query_graphite(self, endpoint: str, method: str = "GET", data: dict = None):
        """
        Query the Graphite API.
        """
        config = self.config.authentication

        url = f"{config.host_url.rstrip('/')}/{endpoint}"

        headers = {
            "Content-Type": "application/json",
        }

        # Add API key if provided
        if hasattr(config, 'api_key') and config.api_key:
            headers["Authorization"] = f"Bearer {config.api_key}"

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
            raise ProviderException(f"Failed to query Graphite API: {e}")

    def _get_alerts(self) -> list[AlertDto]:
        """
        Get alerts from Graphite (query anomaly detection).
        """
        self.logger.info("Getting alerts from Graphite")

        try:
            alerts = []

            # Query Graphite events for alerts
            response = self._query_graphite("events/get_tags?limit=100")

            if response.status_code == 200:
                data = response.json()
                for event in data:
                    alert = self._parse_event(event)
                    if alert:
                        alerts.append(alert)

            self.logger.info(f"Retrieved {len(alerts)} alerts from Graphite")
            return alerts

        except Exception as e:
            self.logger.error(f"Failed to get alerts from Graphite: {e}")
            raise ProviderException(f"Failed to get alerts from Graphite: {e}")

    def _parse_event(self, event: dict) -> AlertDto:
        """
        Parse a Graphite event into an AlertDto.
        """
        # Extract event information
        what = event.get("what", "Unknown Event")
        tags = event.get("tags", [])
        when = event.get("when", "")
        data = event.get("data", "")

        # Determine severity based on tags
        severity = AlertSeverity.INFO
        if isinstance(tags, list):
            tags_str = " ".join(tags).lower()
        else:
            tags_str = str(tags).lower()

        if any(word in tags_str for word in ["critical", "crit", "severe"]):
            severity = AlertSeverity.CRITICAL
        elif any(word in tags_str for word in ["warning", "warn"]):
            severity = AlertSeverity.WARNING
        elif any(word in tags_str for word in ["ok", "resolved", "healthy"]):
            severity = AlertSeverity.LOW

        # Determine status
        status = AlertStatus.FIRING
        if severity == AlertSeverity.LOW or "resolved" in tags_str:
            status = AlertStatus.RESOLVED

        return AlertDto(
            id=f"graphite-{event.get('id', what)}",
            name=f"Graphite Event: {what}",
            status=status,
            severity=severity,
            lastReceived=datetime.datetime.now().isoformat(),
            description=f"{what}\n{data}",
            source=["graphite"],
            labels={
                "what": what,
                "tags": str(tags),
                "when": when,
            },
        )

    def get_alerts(self) -> list[AlertDto]:
        """
        Get alerts from Graphite.
        """
        return self._get_alerts()

    def notify(self, alert: AlertDto | dict = None):
        """
        Notify Graphite about an alert (not implemented).
        """
        raise ProviderException("Graphite provider does not support sending alerts")

    def setup_webhook(
        self, tenant_id: str, keep_api_url: str, api_key: str, setup_alerts: bool = True
    ):
        """
        Setup webhook for Graphite (not applicable).
        """
        raise ProviderException("Webhooks are not supported for Graphite provider")
