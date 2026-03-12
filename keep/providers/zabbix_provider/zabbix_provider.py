"""
ZabbixProvider is a class that provides a way to read alerts from Zabbix.
"""

import dataclasses
import datetime
import os

import pydantic
import requests

from keep.api.models.alert import AlertDto, AlertSeverity, AlertStatus
from keep.contextmanager.contextmanager import ContextManager
from keep.providers.base.base_provider import BaseProvider, ProviderHealthMixin
from keep.providers.models.provider_config import ProviderConfig, ProviderScope


@pydantic.dataclasses.dataclass
class ZabbixProviderAuthConfig:
    url: pydantic.AnyHttpUrl = dataclasses.field(
        metadata={
            "required": True,
            "description": "Zabbix server URL",
            "hint": "https://zabbix.example.com",
            "validation": "any_http_url",
        }
    )
    api_token: str = dataclasses.field(
        metadata={
            "description": "Zabbix API token",
            "sensitive": True,
            "required": True,
        }
    )
    verify: bool = dataclasses.field(
        metadata={
            "description": "Verify SSL certificates",
            "hint": "Set to false to allow self-signed certificates",
            "sensitive": False,
        },
        default=True,
    )


class ZabbixProvider(BaseProvider, ProviderHealthMixin):
    """Get alerts from Zabbix into Keep."""

    PROVIDER_CATEGORY = ["Monitoring"]
    PROVIDER_DISPLAY_NAME = "Zabbix"
    
    SEVERITIES_MAP = {
        "disaster": AlertSeverity.CRITICAL,
        "high": AlertSeverity.CRITICAL,
        "average": AlertSeverity.HIGH,
        "warning": AlertSeverity.WARNING,
        "information": AlertSeverity.INFO,
        "not_classified": AlertSeverity.LOW,
    }

    STATUS_MAP = {
        "problem": AlertStatus.FIRING,
        "ok": AlertStatus.RESOLVED,
    }

    PROVIDER_SCOPES = [
        ProviderScope(
            name="connectivity",
            description="Connectivity Test",
            mandatory=True
        )
    ]

    def __init__(
        self, context_manager: ContextManager, provider_id: str, config: ProviderConfig
    ):
        super().__init__(context_manager, provider_id, config)
    
    def dispose(self):
        """Dispose the provider."""
        pass
    
    def validate_config(self):
        """Validate the provider configuration."""
        self.logger.info("Validating Zabbix provider config")
        pass
    
    def _get_alerts(self):
        """Get alerts from Zabbix."""
        try:
            auth_config = ZabbixProviderAuthConfig(**self.authentication_config)
            headers = {
                "Authorization": f"Bearer {auth_config.api_token}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            # Use Zabbix API to get triggers/problems
            payload = {
                "jsonrpc": "2.0",
                "method": "problem.get",
                "params": {
                    "output": ["eventid", "name", "severity", "status"],
                    "selectAcknowledges": "extend",
                    "selectTags": "extend",
                    "selectHosts": ["hostid", "name"],
                    "sortfield": "eventid",
                    "sortorder": "DESC",
                    "recent": "true"
                },
                "auth": auth_config.api_token,
                "id": 1
            }
            
            response = requests.post(
                f"{auth_config.url}/api_jsonrpc.php",
                headers=headers,
                json=payload,
                verify=auth_config.verify,
                timeout=10
            )
            
            if response.status_code != 200:
                self.logger.error(f"Failed to fetch alerts: {response.status_code}")
                return []
            
            data = response.json()
            alerts = []
            
            for problem in data.get('result', []):
                alert = AlertDto(
                    title=f"Zabbix Alert: {problem.get('name', 'Unknown')}",
                    description=problem.get('name', ''),
                    severity=self.SEVERITIES_MAP.get(
                        str(problem.get('severity', '0')),
                        AlertSeverity.INFO
                    ),
                    status=self.STATUS_MAP.get(
                        problem.get('status', 'problem'),
                        AlertStatus.FIRING
                    ),
                    source="zabbix",
                    url=f"{auth_config.url}/tr_events.php?triggerid={problem.get('objectid', '')}",
                    labels={
                        "eventid": str(problem.get('eventid', '')),
                        "host": problem.get('hosts', [{}])[0].get('name', '') if problem.get('hosts') else '',
                        "severity": str(problem.get('severity', '')),
                    },
                    lastReceived=datetime.datetime.now().isoformat(),
                )
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Error fetching Zabbix alerts: {e}")
            return []

if __name__ == "__main__":
    print("Zabbix Provider loaded successfully")
