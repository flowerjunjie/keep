"""
BetterUptimeProvider is a class that provides a set of methods to interact with 网站监控服务.
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
class BetterUptimeProviderAuthConfig:
    """
    BetterUptimeProviderAuthConfig is a class that holds the authentication information for the BetterUptimeProvider.
    """

    host_url: pydantic.AnyHttpUrl = dataclasses.field(
        metadata={
            "required": True,
            "description": "BetterUptime Host URL or API endpoint",
            "sensitive": False,
            "validation": "any_http_url",
        },
    )

    api_token: str = dataclasses.field(
        metadata={
            "required": True,
            "description": "BetterUptime API Token",
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


class BetterUptimeProvider(BaseProvider):
    PROVIDER_DISPLAY_NAME = "BetterUptime"
    PROVIDER_TAGS = ["alert", "monitoring"]
    PROVIDER_CATEGORY = ["Monitoring"]
    PROVIDER_SCOPES = [
        ProviderScope(name="authenticated", description="User is authenticated"),
    ]

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
        Validates the configuration of the BetterUptime provider.
        """
        self.logger.info("Validating BetterUptime provider configuration")

        try:
            # Test authentication
            response = self._query_betteruptime("api/v1/status")

            if response.status_code in [200, 204]:
                self.logger.info("BetterUptime provider configuration is valid")
                return {"authenticated": True}
            else:
                raise ProviderException(
                    f"Failed to connect to BetterUptime: {response.status_code}"
                )
        except Exception as e:
            self.logger.error(f"Failed to validate BetterUptime configuration: {e}")
            raise ProviderException(f"Failed to validate BetterUptime configuration: {e}")

    def _query_betteruptime(self, endpoint: str, method: str = "GET", data: dict = None):
        """
        Query the BetterUptime API.
        """
        config = self.config.authentication

        url = f"{config.host_url.rstrip('/')}/{endpoint}"

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
            raise ProviderException(f"Failed to query BetterUptime API: {e}")

    def _get_alerts(self) -> list[AlertDto]:
        """
        Get alerts from BetterUptime.
        """
        self.logger.info("Getting alerts from BetterUptime")

        try:
            alerts = []

            # Query for alerts
            response = self._query_betteruptime("api/v1/alerts")

            if response.status_code == 200:
                data = response.json()
                for alert_data in data.get("alerts", []):
                    alert = self._parse_alert(alert_data)
                    if alert:
                        alerts.append(alert)

            self.logger.info(f"Retrieved {len(alerts)} alerts from BetterUptime")
            return alerts

        except Exception as e:
            self.logger.error(f"Failed to get alerts from BetterUptime: {e}")
            raise ProviderException(f"Failed to get alerts from BetterUptime: {e}")

    def _parse_alert(self, alert_data: dict) -> AlertDto:
        """
        Parse an alert from BetterUptime.
        """
        alert_name = alert_data.get("name", "Unknown Alert")
        status_str = alert_data.get("status", "firing")
        severity_str = alert_data.get("severity", "info")

        # Map status and severity
        status = AlertStatus.FIRING if status_str != "resolved" else AlertStatus.RESOLVED

        severity = AlertSeverity.INFO
        if severity_str == "critical":
            severity = AlertSeverity.CRITICAL
        elif severity_str == "warning":
            severity = AlertSeverity.WARNING
        elif severity_str == "ok":
            severity = AlertSeverity.LOW

        return AlertDto(
            id=f"betteruptime-{alert_data.get('id', 'unknown')}",
            name=f"{Display_Name}: {alert_name}",
            status=status,
            severity=severity,
            lastReceived=datetime.datetime.now().isoformat(),
            description=alert_data.get("description", "No description"),
            source=["betteruptime"],
            labels={
                "provider": "betteruptime",
                "id": alert_data.get('id', 'unknown'),
            },
        )

    def get_alerts(self) -> list[AlertDto]:
        """
        Get alerts from BetterUptime.
        """
        return self._get_alerts()

    def notify(self, alert: AlertDto | dict = None):
        """
        Notify BetterUptime about an alert (not implemented).
        """
        raise ProviderException("BetterUptime provider does not support sending alerts")

    def setup_webhook(
        self, tenant_id: str, keep_api_url: str, api_key: str, setup_alerts: bool = True
    ):
        """
        Setup webhook for BetterUptime (not applicable).
        """
        raise ProviderException("Webhooks are not supported for BetterUptime provider")
