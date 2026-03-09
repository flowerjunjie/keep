"""
LogstashProvider is a class that provides a set of methods to interact with Logstash.
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
class LogstashProviderAuthConfig:
    """
    LogstashProviderAuthConfig is a class that holds the authentication information for the LogstashProvider.
    """

    host_url: pydantic.AnyHttpUrl = dataclasses.field(
        metadata={
            "required": True,
            "description": "Logstash Host URL (e.g., https://logstash.example.com)",
            "sensitive": False,
            "validation": "any_http_url",
        },
    )

    username: str = dataclasses.field(
        metadata={
            "required": False,
            "description": "Logstash username (if authentication is enabled)",
            "sensitive": False,
        },
        default=None,
    )

    password: str = dataclasses.field(
        metadata={
            "required": False,
            "description": "Logstash password",
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


class LogstashProvider(BaseProvider):
    PROVIDER_DISPLAY_NAME = "Logstash"
    PROVIDER_TAGS = ["alert", "monitoring", "logging"]
    PROVIDER_CATEGORY = ["Monitoring", "Logging"]
    PROVIDER_SCOPES = [
        ProviderScope(name="authenticated", description="User is authenticated"),
    ]

    """
    Logstash log states mapping
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
        Validates the configuration of the Logstash provider.
        """
        self.logger.info("Validating Logstash provider configuration")

        try:
            # Test by querying Logstash stats
            response = self._query_logstash("_node/stats")

            if response.status_code == 200:
                self.logger.info("Logstash provider configuration is valid")
                return {"authenticated": True}
            else:
                raise ProviderException(
                    f"Failed to connect to Logstash: {response.status_code}"
                )
        except Exception as e:
            self.logger.error(f"Failed to validate Logstash configuration: {e}")
            raise ProviderException(f"Failed to validate Logstash configuration: {e}")

    def _query_logstash(self, endpoint: str, method: str = "GET", data: dict = None):
        """
        Query the Logstash API.
        """
        config = self.config.authentication

        url = f"{config.host_url.rstrip('/')}/{endpoint}"

        headers = {
            "Content-Type": "application/json",
        }

        # Add authentication if provided
        auth = None
        if hasattr(config, 'username') and hasattr(config, 'password') and config.username and config.password:
            auth = (config.username, config.password)

        params = {
            "verify_ssl": config.verify_ssl if hasattr(config, 'verify_ssl') else True
        }

        try:
            if method == "GET":
                response = requests.get(url, headers=headers, auth=auth, params=params)
            elif method == "POST":
                response = requests.post(url, headers=headers, auth=auth, json=data, params=params)
            else:
                raise ProviderException(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            raise ProviderException(f"Failed to query Logstash API: {e}")

    def _get_alerts(self) -> list[AlertDto]:
        """
        Get alerts from Logstash (error logs).
        """
        self.logger.info("Getting alerts from Logstash")

        try:
            alerts = []

            # Query Logstash for error events
            # Note: Logstash doesn't have a built-in alerting API, so we'd typically
            # query an external store like Elasticsearch where Logstash sends events
            # For this provider, we'll simulate by checking Logstash pipeline health

            response = self._query_logstash("_node/stats/pipelines")

            if response.status_code == 200:
                data = response.json()
                for pipeline_name, pipeline_stats in data.items():
                    alert = self._parse_pipeline_stats(pipeline_name, pipeline_stats)
                    if alert:
                        alerts.append(alert)

            self.logger.info(f"Retrieved {len(alerts)} alerts from Logstash")
            return alerts

        except Exception as e:
            self.logger.error(f"Failed to get alerts from Logstash: {e}")
            raise ProviderException(f"Failed to get alerts from Logstash: {e}")

    def _parse_pipeline_stats(self, pipeline_name: str, stats: dict) -> AlertDto:
        """
        Parse Logstash pipeline stats into an AlertDto.
        """
        # Check for errors in pipeline
        events = stats.get("events", {})
        errors = events.get("in", 0) - events.get("out", 0)

        # Check if pipeline is dead
        is_dead = stats.get("hash", "") == "dead"

        if errors > 0 or is_dead:
            severity = AlertSeverity.CRITICAL if is_dead else AlertSeverity.WARNING

            return AlertDto(
                id=f"logstash-{pipeline_name}",
                name=f"Logstash Pipeline Alert: {pipeline_name}",
                status=AlertStatus.FIRING,
                severity=severity,
                lastReceived=datetime.datetime.now().isoformat(),
                description=f"Pipeline '{pipeline_name}' has {errors} errors" if not is_dead else f"Pipeline '{pipeline_name}' is dead",
                source=["logstash"],
                labels={
                    "pipeline": pipeline_name,
                    "errors": str(errors),
                    "dead": str(is_dead),
                },
            )

        return None

    def get_alerts(self) -> list[AlertDto]:
        """
        Get alerts from Logstash.
        """
        return self._get_alerts()

    def notify(self, alert: AlertDto | dict = None):
        """
        Notify Logstash about an alert (not implemented).
        """
        raise ProviderException("Logstash provider does not support sending alerts")

    def setup_webhook(
        self, tenant_id: str, keep_api_url: str, api_key: str, setup_alerts: bool = True
    ):
        """
        Setup webhook for Logstash (not applicable).
        """
        raise ProviderException("Webhooks are not supported for Logstash provider")
