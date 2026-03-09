"""
JaegerProvider is a class that provides a set of methods to interact with Jaeger tracing.
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
class JaegerProviderAuthConfig:
    """
    JaegerProviderAuthConfig is a class that holds the authentication information for the JaegerProvider.
    """

    host_url: pydantic.AnyHttpUrl = dataclasses.field(
        metadata={
            "required": True,
            "description": "Jaeger Host URL (e.g., https://jaeger.example.com)",
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


class JaegerProvider(BaseProvider):
    PROVIDER_DISPLAY_NAME = "Jaeger"
    PROVIDER_TAGS = ["alert", "monitoring", "tracing"]
    PROVIDER_CATEGORY = ["Monitoring", "Tracing"]
    PROVIDER_SCOPES = [
        ProviderScope(name="authenticated", description="User is authenticated"),
    ]

    """
    Jaeger trace states mapping
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
        Validates the configuration of the Jaeger provider.
        """
        self.logger.info("Validating Jaeger provider configuration")

        try:
            # Test by querying Jaeger API
            response = self._query_jaeger("api/services")

            if response.status_code == 200:
                self.logger.info("Jaeger provider configuration is valid")
                return {"authenticated": True}
            else:
                raise ProviderException(
                    f"Failed to connect to Jaeger: {response.status_code}"
                )
        except Exception as e:
            self.logger.error(f"Failed to validate Jaeger configuration: {e}")
            raise ProviderException(f"Failed to validate Jaeger configuration: {e}")

    def _query_jaeger(self, endpoint: str, method: str = "GET", data: dict = None):
        """
        Query the Jaeger API.
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
            raise ProviderException(f"Failed to query Jaeger API: {e}")

    def _get_alerts(self) -> list[AlertDto]:
        """
        Get alerts from Jaeger (trace-based anomalies).
        """
        self.logger.info("Getting alerts from Jaeger")

        try:
            alerts = []

            # Query for error traces in the last hour
            response = self._query_jaeger("api/traces?lookback=1h&limit=20")

            if response.status_code == 200:
                data = response.json()
                for trace in data.get("data", []):
                    alert = self._parse_trace(trace)
                    if alert:
                        alerts.append(alert)

            self.logger.info(f"Retrieved {len(alerts)} alerts from Jaeger")
            return alerts

        except Exception as e:
            self.logger.error(f"Failed to get alerts from Jaeger: {e}")
            raise ProviderException(f"Failed to get alerts from Jaeger: {e}")

    def _parse_trace(self, trace: dict) -> AlertDto:
        """
        Parse a Jaeger trace into an AlertDto.
        """
        trace_id = trace.get("traceID", "unknown")
        spans = trace.get("spans", [])

        # Count errors in trace
        error_count = 0
        operation_names = []

        for span in spans:
            if "error" in span.get("logs", []).__str__().lower():
                error_count += 1
            operation_names.append(span.get("operationName", "unknown"))

        # Only alert if there are errors
        if error_count == 0:
            return None

        severity = AlertSeverity.CRITICAL if error_count > 1 else AlertSeverity.WARNING

        return AlertDto(
            id=f"jaeger-{trace_id}",
            name=f"Jaeger Trace Errors: {error_count} errors detected",
            status=AlertStatus.FIRING,
            severity=severity,
            lastReceived=datetime.datetime.now().isoformat(),
            description=f"Trace contains {error_count} error spans. Operations: {', '.join(set(operation_names))}",
            source=["jaeger"],
            labels={
                "trace_id": trace_id,
                "error_count": str(error_count),
                "operations": ", ".join(set(operation_names)),
            },
        )

    def get_alerts(self) -> list[AlertDto]:
        """
        Get alerts from Jaeger.
        """
        return self._get_alerts()

    def notify(self, alert: AlertDto | dict = None):
        """
        Notify Jaeger about an alert (not implemented).
        """
        raise ProviderException("Jaeger provider does not support sending alerts")

    def setup_webhook(
        self, tenant_id: str, keep_api_url: str, api_key: str, setup_alerts: bool = True
    ):
        """
        Setup webhook for Jaeger (not applicable).
        """
        raise ProviderException("Webhooks are not supported for Jaeger provider")
