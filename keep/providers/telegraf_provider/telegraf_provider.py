"""
TelegrafProvider is a class that provides a set of methods to interact with Telegraf metrics.
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
class TelegrafProviderAuthConfig:
    """
    TelegrafProviderAuthConfig is a class that holds the authentication information for the TelegrafProvider.
    """

    host_url: pydantic.AnyHttpUrl = dataclasses.field(
        metadata={
            "required": True,
            "description": "Telegraf Host URL or InfluxDB URL (e.g., https://influxdb.example.com)",
            "sensitive": False,
            "validation": "any_http_url",
        },
    )

    api_token: str = dataclasses.field(
        metadata={
            "required": True,
            "description": "InfluxDB API Token (for Telegraf metrics)",
            "sensitive": True,
        },
        default=None,
    )

    org: str = dataclasses.field(
        metadata={
            "required": True,
            "description": "InfluxDB Organization name",
            "sensitive": False,
        },
        default=None,
    )

    bucket: str = dataclasses.field(
        metadata={
            "required": False,
            "description": "Telegraf bucket name",
            "sensitive": False,
        },
        default="telegraf",
    )

    verify_ssl: bool = dataclasses.field(
        metadata={
            "required": False,
            "description": "Verify SSL certificate",
            "sensitive": False,
        },
        default=True,
    )


class TelegrafProvider(BaseProvider):
    PROVIDER_DISPLAY_NAME = "Telegraf"
    PROVIDER_TAGS = ["alert", "monitoring", "metrics"]
    PROVIDER_CATEGORY = ["Monitoring", "Metrics"]
    PROVIDER_SCOPES = [
        ProviderScope(name="authenticated", description="User is authenticated"),
    ]

    """
    Telegraf metric states mapping
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
        Validates the configuration of the Telegraf provider.
        """
        self.logger.info("Validating Telegraf provider configuration")

        try:
            # Test authentication by querying InfluxDB (Telegraf storage)
            config = self.config.authentication
            response = self._query_telegraf_storage("buckets")

            if response.status_code in [200, 204]:
                self.logger.info("Telegraf provider configuration is valid")
                return {"authenticated": True}
            else:
                raise ProviderException(
                    f"Failed to authenticate with Telegraf storage: {response.status_code}"
                )
        except Exception as e:
            self.logger.error(f"Failed to validate Telegraf configuration: {e}")
            raise ProviderException(f"Failed to validate Telegraf configuration: {e}")

    def _query_telegraf_storage(self, endpoint: str, method: str = "GET", data: dict = None):
        """
        Query the InfluxDB API (Telegraf storage backend).
        """
        config = self.config.authentication

        url = f"{config.host_url.rstrip('/')}/api/v2/{endpoint}"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {config.api_token}",
        }

        params = {
            "org": config.org,
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
            raise ProviderException(f"Failed to query Telegraf storage API: {e}")

    def _get_alerts(self) -> list[AlertDto]:
        """
        Get alerts from Telegraf metrics.
        """
        self.logger.info("Getting alerts from Telegraf")

        try:
            # Query Telegraf bucket for anomaly/exception metrics
            alerts = []

            # Query for critical/warning metrics
            config = self.config.authentication
            bucket = config.bucket if hasattr(config, 'bucket') else "telegraf"

            # Flux query to find anomalous metrics
            flux_query = f'''
            from(bucket: "{bucket}")
              |> range(start: -5m)
              |> filter(fn: (r) => r["_measurement"] =~ /alert|error|exception|fail/)
              |> group()
              |> distinct(column: "_field")
            '''

            response = self._query_telegraf_storage("query", method="POST", data={"query": flux_query})

            if response.status_code == 200:
                data = response.json()
                # Parse results
                for record in data:
                    alert = self._parse_metric(record)
                    if alert:
                        alerts.append(alert)

            self.logger.info(f"Retrieved {len(alerts)} alerts from Telegraf")
            return alerts

        except Exception as e:
            self.logger.error(f"Failed to get alerts from Telegraf: {e}")
            raise ProviderException(f"Failed to get alerts from Telegraf: {e}")

    def _parse_metric(self, metric: dict) -> AlertDto:
        """
        Parse a Telegraf metric into an AlertDto.
        """
        # Extract metric information
        measurement = metric.get("_measurement", "unknown")
        field = metric.get("_field", "unknown")
        value = metric.get("_value", 0)

        # Determine severity based on field name
        severity = AlertSeverity.INFO
        field_lower = field.lower()
        if any(word in field_lower for word in ["critical", "crit", "fatal", "error"]):
            severity = AlertSeverity.CRITICAL
        elif any(word in field_lower for word in ["warning", "warn"]):
            severity = AlertSeverity.WARNING
        elif any(word in field_lower for word in ["ok", "healthy", "success"]):
            severity = AlertSeverity.LOW

        # Determine status
        status = AlertStatus.FIRING
        if severity in [AlertSeverity.LOW]:
            status = AlertStatus.RESOLVED

        return AlertDto(
            id=f"telegraf-{measurement}-{field}",
            name=f"Telegraf Alert: {measurement} - {field}",
            status=status,
            severity=severity,
            lastReceived=datetime.datetime.now().isoformat(),
            description=f"Telegraf metric: {field} = {value}",
            source=["telegraf"],
            labels={
                "measurement": measurement,
                "field": field,
                "value": str(value),
            },
        )

    def get_alerts(self) -> list[AlertDto]:
        """
        Get alerts from Telegraf.
        """
        return self._get_alerts()

    def notify(self, alert: AlertDto | dict = None):
        """
        Notify Telegraf about an alert (not implemented).
        """
        raise ProviderException("Telegraf provider does not support sending alerts")

    def setup_webhook(
        self, tenant_id: str, keep_api_url: str, api_key: str, setup_alerts: bool = True
    ):
        """
        Setup webhook for Telegraf (not applicable).
        """
        raise ProviderException("Webhooks are not supported for Telegraf provider")
