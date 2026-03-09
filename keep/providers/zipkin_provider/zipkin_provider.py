"""
ZipkinProvider is a class that provides a set of methods to interact with Zipkin tracing.
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
class ZipkinProviderAuthConfig:
    """
    ZipkinProviderAuthConfig is a class that holds the authentication information for the ZipkinProvider.
    """

    host_url: pydantic.AnyHttpUrl = dataclasses.field(
        metadata={
            "required": True,
            "description": "Zipkin Host URL (e.g., https://zipkin.example.com)",
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


class ZipkinProvider(BaseProvider):
    PROVIDER_DISPLAY_NAME = "Zipkin"
    PROVIDER_TAGS = ["alert", "monitoring", "tracing"]
    PROVIDER_CATEGORY = ["Monitoring", "Tracing"]
    PROVIDER_SCOPES = [
        ProviderScope(name="authenticated", description="User is authenticated"),
    ]

    """
    Zipkin trace states mapping
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
        Validates the configuration of the Zipkin provider.
        """
        self.logger.info("Validating Zipkin provider configuration")

        try:
            # Test by querying Zipkin API
            response = self._query_zipkin("api/v2/services")

            if response.status_code == 200:
                self.logger.info("Zipkin provider configuration is valid")
                return {"authenticated": True}
            else:
                raise ProviderException(
                    f"Failed to connect to Zipkin: {response.status_code}"
                )
        except Exception as e:
            self.logger.error(f"Failed to validate Zipkin configuration: {e}")
            raise ProviderException(f"Failed to validate Zipkin configuration: {e}")

    def _query_zipkin(self, endpoint: str, method: str = "GET", data: dict = None):
        """
        Query the Zipkin API.
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
            raise ProviderException(f"Failed to query Zipkin API: {e}")

    def _get_alerts(self) -> list[AlertDto]:
        """
        Get alerts from Zipkin (trace-based anomalies).
        """
        self.logger.info("Getting alerts from Zipkin")

        try:
            alerts = []

            # Query for error traces
            # Zipkin API doesn't have direct error filtering, so we'll query recent traces
            end_ts = int(datetime.datetime.now().timestamp() * 1000000)
            start_ts = end_ts - (3600 * 1000000)  # 1 hour ago

            response = self._query_zipkin(f"api/v2/traces?lookback=3600000&limit=20")

            if response.status_code == 200:
                traces = response.json()
                for trace in traces:
                    alert = self._parse_trace(trace)
                    if alert:
                        alerts.append(alert)

            self.logger.info(f"Retrieved {len(alerts)} alerts from Zipkin")
            return alerts

        except Exception as e:
            self.logger.error(f"Failed to get alerts from Zipkin: {e}")
            raise ProviderException(f"Failed to get alerts from Zipkin: {e}")

    def _parse_trace(self, trace: list) -> AlertDto:
        """
        Parse a Zipkin trace into an AlertDto.
        """
        if not trace or len(trace) == 0:
            return None

        trace_id = trace[0].get("traceId", "unknown")

        # Count errors in trace
        error_count = 0
        service_names = set()
        operation_names = []

        for span in trace:
            tags = span.get("tags", {})
            if tags.get("error") or "error" in tags.get("http.status_code", "").lower():
                error_count += 1

            service_names.add(span.get("localEndpoint", {}).get("serviceName", "unknown"))
            operation_names.append(span.get("name", "unknown"))

        # Only alert if there are errors
        if error_count == 0:
            return None

        severity = AlertSeverity.CRITICAL if error_count > 1 else AlertSeverity.WARNING

        return AlertDto(
            id=f"zipkin-{trace_id}",
            name=f"Zipkin Trace Errors: {error_count} errors detected",
            status=AlertStatus.FIRING,
            severity=severity,
            lastReceived=datetime.datetime.now().isoformat(),
            description=f"Trace contains {error_count} error spans. Services: {', '.join(service_names)}",
            source=["zipkin"],
            labels={
                "trace_id": trace_id,
                "error_count": str(error_count),
                "services": ", ".join(service_names),
                "operations": ", ".join(set(operation_names)),
            },
        )

    def get_alerts(self) -> list[AlertDto]:
        """
        Get alerts from Zipkin.
        """
        return self._get_alerts()

    def notify(self, alert: AlertDto | dict = None):
        """
        Notify Zipkin about an alert (not implemented).
        """
        raise ProviderException("Zipkin provider does not support sending alerts")

    def setup_webhook(
        self, tenant_id: str, keep_api_url: str, api_key: str, setup_alerts: bool = True
    ):
        """
        Setup webhook for Zipkin (not applicable).
        """
        raise ProviderException("Webhooks are not supported for Zipkin provider")
