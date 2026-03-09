"""
FluentdProvider is a class that provides a set of methods to interact with Fluentd.
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
class FluentdProviderAuthConfig:
    """
    FluentdProviderAuthConfig is a class that holds the authentication information for the FluentdProvider.
    """

    host_url: pydantic.AnyHttpUrl = dataclasses.field(
        metadata={
            "required": True,
            "description": "Fluentd Host URL (e.g., https://fluentd.example.com)",
            "sensitive": False,
            "validation": "any_http_url",
        },
    )

    verify_ssl: bool = dataclasses.field(
        metadata={
            "required": False,
            "description": "Verify SSL certificate",
            "sensitive": False,
        },
        default=True,
    )


class FluentdProvider(BaseProvider):
    PROVIDER_DISPLAY_NAME = "Fluentd"
    PROVIDER_TAGS = ["alert", "monitoring", "logging"]
    PROVIDER_CATEGORY = ["Monitoring", "Logging"]
    PROVIDER_SCOPES = [
        ProviderScope(name="authenticated", description="User is authenticated"),
    ]

    """
    Fluentd log states mapping
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
        Validates the configuration of the Fluentd provider.
        """
        self.logger.info("Validating Fluentd provider configuration")

        try:
            # Test by querying Fluentd API
            response = self._query_fluentd("api/plugins.json")

            if response.status_code == 200:
                self.logger.info("Fluentd provider configuration is valid")
                return {"authenticated": True}
            else:
                raise ProviderException(
                    f"Failed to connect to Fluentd: {response.status_code}"
                )
        except Exception as e:
            self.logger.error(f"Failed to validate Fluentd configuration: {e}")
            raise ProviderException(f"Failed to validate Fluentd configuration: {e}")

    def _query_fluentd(self, endpoint: str, method: str = "GET", data: dict = None):
        """
        Query the Fluentd API.
        """
        config = self.config.authentication

        url = f"{config.host_url.rstrip('/')}/{endpoint}"

        headers = {
            "Content-Type": "application/json",
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
            raise ProviderException(f"Failed to query Fluentd API: {e}")

    def _get_alerts(self) -> list[AlertDto]:
        """
        Get alerts from Fluentd (error logs and plugin issues).
        """
        self.logger.info("Getting alerts from Fluentd")

        try:
            alerts = []

            # Query Fluentd plugins for errors
            response = self._query_fluentd("api/plugins.json")

            if response.status_code == 200:
                data = response.json()
                plugins = data.get("plugins", [])

                for plugin in plugins:
                    alert = self._parse_plugin_status(plugin)
                    if alert:
                        alerts.append(alert)

            self.logger.info(f"Retrieved {len(alerts)} alerts from Fluentd")
            return alerts

        except Exception as e:
            self.logger.error(f"Failed to get alerts from Fluentd: {e}")
            raise ProviderException(f"Failed to get alerts from Fluentd: {e}")

    def _parse_plugin_status(self, plugin: dict) -> AlertDto:
        """
        Parse Fluentd plugin status into an AlertDto.
        """
        plugin_id = plugin.get("plugin_id", "unknown")
        plugin_type = plugin.get("type", "unknown")
        retry_count = plugin.get("retry_count", 0)

        # Check for high retry count (indicates errors)
        if retry_count > 10:
            severity = AlertSeverity.CRITICAL if retry_count > 50 else AlertSeverity.WARNING

            return AlertDto(
                id=f"fluentd-{plugin_id}",
                name=f"Fluentd Plugin Alert: {plugin_type}",
                status=AlertStatus.FIRING,
                severity=severity,
                lastReceived=datetime.datetime.now().isoformat(),
                description=f"Plugin '{plugin_type}' has {retry_count} retries",
                source=["fluentd"],
                labels={
                    "plugin_id": plugin_id,
                    "plugin_type": plugin_type,
                    "retry_count": str(retry_count),
                },
            )

        return None

    def get_alerts(self) -> list[AlertDto]:
        """
        Get alerts from Fluentd.
        """
        return self._get_alerts()

    def notify(self, alert: AlertDto | dict = None):
        """
        Notify Fluentd about an alert (not implemented).
        """
        raise ProviderException("Fluentd provider does not support sending alerts")

    def setup_webhook(
        self, tenant_id: str, keep_api_url: str, api_key: str, setup_alerts: bool = True
    ):
        """
        Setup webhook for Fluentd (not applicable).
        """
        raise ProviderException("Webhooks are not supported for Fluentd provider")
