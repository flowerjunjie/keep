"""
InfluxDBProvider is a class that provides a set of methods to interact with InfluxDB.
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
class InfluxDBProviderAuthConfig:
    """
    InfluxDBProviderAuthConfig is a class that holds the authentication information for the InfluxDBProvider.
    """

    host_url: pydantic.AnyHttpUrl = dataclasses.field(
        metadata={
            "required": True,
            "description": "InfluxDB Host URL (e.g., https://influxdb.example.com)",
            "sensitive": False,
            "validation": "any_http_url",
        },
    )

    api_token: str = dataclasses.field(
        metadata={
            "required": True,
            "description": "InfluxDB API Token",
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
            "description": "InfluxDB Bucket name",
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


class InfluxDBProvider(BaseProvider):
    PROVIDER_DISPLAY_NAME = "InfluxDB"
    PROVIDER_TAGS = ["alert", "monitoring", "database"]
    PROVIDER_CATEGORY = ["Monitoring", "Database"]
    PROVIDER_SCOPES = [
        ProviderScope(name="authenticated", description="User is authenticated"),
    ]

    """
    InfluxDB alert states mapping
    """

    STATUS_MAP = {
        "firing": AlertStatus.FIRING,
        "resolved": AlertStatus.RESOLVED,
        "pending": AlertStatus.PENDING,
    }

    SEVERITY_MAP = {
        "crit": AlertSeverity.CRITICAL,
        "critical": AlertSeverity.CRITICAL,
        "warn": AlertSeverity.WARNING,
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
        Validates the configuration of the InfluxDB provider.
        """
        self.logger.info("Validating InfluxDB provider configuration")

        try:
            # Test authentication by querying buckets
            config = self.config.authentication
            response = self._query_influxdb("buckets")

            if response.status_code in [200, 204]:
                self.logger.info("InfluxDB provider configuration is valid")
                return {"authenticated": True}
            else:
                raise ProviderException(
                    f"Failed to authenticate with InfluxDB: {response.status_code}"
                )
        except Exception as e:
            self.logger.error(f"Failed to validate InfluxDB configuration: {e}")
            raise ProviderException(f"Failed to validate InfluxDB configuration: {e}")

    def _query_influxdb(self, endpoint: str, method: str = "GET", data: dict = None):
        """
        Query the InfluxDB API.
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
            raise ProviderException(f"Failed to query InfluxDB API: {e}")

    def _get_alerts(self) -> list[AlertDto]:
        """
        Get alerts from InfluxDB (query check data).
        """
        self.logger.info("Getting alerts from InfluxDB")

        try:
            # Query tasks/alerts from InfluxDB
            response = self._query_influxdb("tasks?limit=100")

            alerts = []

            if response.status_code == 200:
                data = response.json()
                for task in data.get("tasks", []):
                    # Filter for alert/check tasks
                    if task.get("type") == "alert":
                        alert = self._parse_task(task)
                        if alert:
                            alerts.append(alert)

            self.logger.info(f"Retrieved {len(alerts)} alerts from InfluxDB")
            return alerts

        except Exception as e:
            self.logger.error(f"Failed to get alerts from InfluxDB: {e}")
            raise ProviderException(f"Failed to get alerts from InfluxDB: {e}")

    def _parse_task(self, task: dict) -> AlertDto:
        """
        Parse an InfluxDB alert task into an AlertDto.
        """
        task_name = task.get("name", "Unknown")
        task_id = task.get("id", "unknown")

        # Extract task metadata
        metadata = task.get("metadata", {})
        status = metadata.get("status", "active")

        # Determine alert status
        alert_status = AlertStatus.FIRING
        if status == "inactive":
            alert_status = AlertStatus.RESOLVED
        elif status == "disabled":
            alert_status = AlertStatus.PENDING

        # Determine severity based on task name or tags
        severity = AlertSeverity.INFO
        task_name_lower = task_name.lower()
        if any(word in task_name_lower for word in ["critical", "crit", "fatal"]):
            severity = AlertSeverity.CRITICAL
        elif any(word in task_name_lower for word in ["warning", "warn"]):
            severity = AlertSeverity.WARNING
        elif any(word in task_name_lower for word in ["ok", "healthy"]):
            severity = AlertSeverity.LOW

        return AlertDto(
            id=f"influxdb-{task_id}",
            name=f"InfluxDB Alert: {task_name}",
            status=alert_status,
            severity=severity,
            lastReceived=datetime.datetime.now().isoformat(),
            description=f"InfluxDB alert task: {task_name}",
            source=["influxdb"],
            labels={
                "task_id": task_id,
                "task_name": task_name,
                "status": status,
                "type": task.get("type", "unknown"),
            },
        )

    def get_alerts(self) -> list[AlertDto]:
        """
        Get alerts from InfluxDB.
        """
        return self._get_alerts()

    def notify(self, alert: AlertDto | dict = None):
        """
        Notify InfluxDB about an alert (not implemented).
        """
        raise ProviderException("InfluxDB provider does not support sending alerts")

    def setup_webhook(
        self, tenant_id: str, keep_api_url: str, api_key: str, setup_alerts: bool = True
    ):
        """
        Setup webhook for InfluxDB (not applicable).
        """
        raise ProviderException("Webhooks are not supported for InfluxDB provider")
