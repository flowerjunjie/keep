"""
NagiosProvider is a class that provides a set of methods to interact with the Nagios API.
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
class NagiosProviderAuthConfig:
    """
    NagiosProviderAuthConfig is a class that holds the authentication information for the NagiosProvider.
    """

    host_url: pydantic.AnyHttpUrl = dataclasses.field(
        metadata={
            "required": True,
            "description": "Nagios Host URL (e.g., https://nagios.example.com)",
            "sensitive": False,
            "validation": "any_http_url",
        },
    )

    api_token: str = dataclasses.field(
        metadata={
            "required": True,
            "description": "Nagios API Token",
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


class NagiosProvider(BaseProvider):
    PROVIDER_DISPLAY_NAME = "Nagios"
    PROVIDER_TAGS = ["alert", "monitoring"]
    PROVIDER_CATEGORY = ["Monitoring"]
    PROVIDER_SCOPES = [
        ProviderScope(name="authenticated", description="User is authenticated"),
    ]

    """
    Nagios host/service states mapping
    Based on Nagios API documentation
    """

    STATUS_MAP = {
        "DOWN": AlertStatus.FIRING,
        "UNREACHABLE": AlertStatus.FIRING,
        "UP": AlertStatus.RESOLVED,
        "CRITICAL": AlertStatus.FIRING,
        "WARNING": AlertStatus.FIRING,
        "UNKNOWN": AlertStatus.FIRING,
        "OK": AlertStatus.RESOLVED,
        "PENDING": AlertStatus.PENDING,
    }

    SEVERITY_MAP = {
        "CRITICAL": AlertSeverity.CRITICAL,
        "DOWN": AlertSeverity.CRITICAL,
        "WARNING": AlertSeverity.WARNING,
        "UNKNOWN": AlertSeverity.INFO,
        "OK": AlertSeverity.LOW,
        "UP": AlertSeverity.LOW,
        "PENDING": AlertSeverity.INFO,
    }

    def __init__(
        self, context_manager: ContextManager, provider_id: str, config: ProviderConfig
    ):
        super().__init__(context_manager, provider_id, config)

    def dispose(self):
        pass

    def validate_config(self):
        """
        Validates the configuration of the Nagios provider.

        Raises:
            ProviderException: If the configuration is invalid.
        """
        self.logger.info("Validating Nagios provider configuration")
        
        try:
            # Test authentication by fetching Nagios status
            response = self._query_nagios("status")
            
            if response.status_code == 200:
                self.logger.info("Nagios provider configuration is valid")
                return {"authenticated": True}
            else:
                raise ProviderException(
                    f"Failed to authenticate with Nagios: {response.status_code} - {response.text}"
                )
        except Exception as e:
            self.logger.error(f"Failed to validate Nagios configuration: {e}")
            raise ProviderException(f"Failed to validate Nagios configuration: {e}")

    def _query_nagios(self, endpoint: str, method: str = "GET", data: dict = None):
        """
        Query the Nagios API.

        Args:
            endpoint (str): The API endpoint to query.
            method (str): The HTTP method to use (default: GET).
            data (dict): The data to send in the request body.

        Returns:
            requests.Response: The response from the Nagios API.
        """
        config = self.config.authentication
        
        url = f"{config.host_url.rstrip('/')}/api/v1/{endpoint}"
        
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": config.api_token,
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
            raise ProviderException(f"Failed to query Nagios API: {e}")

    def _get_alerts(self) -> list[AlertDto]:
        """
        Get alerts from Nagios.

        Returns:
            list[AlertDto]: A list of alerts from Nagios.
        """
        self.logger.info("Getting alerts from Nagios")
        
        try:
            # Query host and service problems
            hosts_response = self._query_nagios("objects/hosts")
            services_response = self._query_nagios("objects/services")
            
            alerts = []
            
            # Process host alerts
            if hosts_response.status_code == 200:
                hosts_data = hosts_response.json()
                for host in hosts_data.get("result", []):
                    if host.get("state") != "UP":
                        alert = self._parse_host_alert(host)
                        if alert:
                            alerts.append(alert)
            
            # Process service alerts
            if services_response.status_code == 200:
                services_data = services_response.json()
                for service in services_data.get("result", []):
                    if service.get("state") != "OK":
                        alert = self._parse_service_alert(service)
                        if alert:
                            alerts.append(alert)
            
            self.logger.info(f"Retrieved {len(alerts)} alerts from Nagios")
            return alerts
            
        except Exception as e:
            self.logger.error(f"Failed to get alerts from Nagios: {e}")
            raise ProviderException(f"Failed to get alerts from Nagios: {e}")

    def _parse_host_alert(self, host: dict) -> AlertDto:
        """
        Parse a host alert from Nagios.

        Args:
            host (dict): The host data from Nagios.

        Returns:
            AlertDto: The parsed alert.
        """
        status = self.STATUS_MAP.get(host.get("state", "UNKNOWN"), AlertStatus.FIRING)
        severity = self.SEVERITY_MAP.get(host.get("state", "UNKNOWN"), AlertSeverity.INFO)
        
        return AlertDto(
            id=f"nagios-host-{host.get('name', 'unknown')}",
            name=f"Host: {host.get('display_name', host.get('name', 'unknown'))}",
            status=status,
            severity=severity,
            lastReceived=datetime.datetime.now().isoformat(),
            description=host.get("plugin_output", "No output available"),
            source=["nagios"],
            labels={
                "host": host.get("name", "unknown"),
                "type": "host",
                "address": host.get("address", ""),
                "state": host.get("state", "UNKNOWN"),
            },
        )

    def _parse_service_alert(self, service: dict) -> AlertDto:
        """
        Parse a service alert from Nagios.

        Args:
            service (dict): The service data from Nagios.

        Returns:
            AlertDto: The parsed alert.
        """
        status = self.STATUS_MAP.get(service.get("state", "UNKNOWN"), AlertStatus.FIRING)
        severity = self.SEVERITY_MAP.get(service.get("state", "UNKNOWN"), AlertSeverity.INFO)
        
        return AlertDto(
            id=f"nagios-service-{service.get('host_name', 'unknown')}-{service.get('description', 'unknown')}",
            name=f"Service: {service.get('display_name', service.get('description', 'unknown'))}",
            status=status,
            severity=severity,
            lastReceived=datetime.datetime.now().isoformat(),
            description=service.get("plugin_output", "No output available"),
            source=["nagios"],
            labels={
                "host": service.get("host_name", "unknown"),
                "service": service.get("description", "unknown"),
                "type": "service",
                "state": service.get("state", "UNKNOWN"),
            },
        )

    def _get_alerts_schema(self) -> dict:
        """
        Get the schema for Nagios alerts.

        Returns:
            dict: The schema for Nagios alerts.
        """
        return {
            "type": "object",
            "properties": {
                "host": {
                    "type": "string",
                    "description": "Host name",
                },
                "service": {
                    "type": "string",
                    "description": "Service description",
                },
                "state": {
                    "type": "string",
                    "enum": ["OK", "WARNING", "CRITICAL", "UNKNOWN", "UP", "DOWN", "UNREACHABLE"],
                    "description": "Host or service state",
                },
                "output": {
                    "type": "string",
                    "description": "Plugin output",
                },
            },
        }

    def notify(self, alert: AlertDto | dict = None):
        """
        Notify Nagios about an alert (not implemented for this provider).

        Args:
            alert (AlertDto | dict): The alert to notify.

        Raises:
            ProviderException: This method is not supported.
        """
        raise ProviderException("Nagios provider does not support sending alerts")

    def get_alerts(self) -> list[AlertDto]:
        """
        Get alerts from Nagios.

        Returns:
            list[AlertDto]: A list of alerts from Nagios.
        """
        return self._get_alerts()

    def setup_webhook(
        self, tenant_id: str, keep_api_url: str, api_key: str, setup_alerts: bool = True
    ):
        """
        Setup webhook for Nagios (not applicable for this provider).

        Args:
            tenant_id (str): The tenant ID.
            keep_api_url (str): The Keep API URL.
            api_key (str): The API key.
            setup_alerts (bool): Whether to setup alerts.

        Raises:
            ProviderException: Webhooks are not supported for Nagios.
        """
        raise ProviderException("Webhooks are not supported for Nagios provider")
