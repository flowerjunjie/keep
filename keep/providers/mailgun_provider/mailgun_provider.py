"""
Mailgun Provider for Keep
Category: email
Base URL: https://api.mailgun.net
"""

from typing import Any, Dict
from pydantic import BaseModel, Field


class MailgunConfig(BaseModel):
    """Mailgun configuration"""
    api_key: str = Field(..., description="Mailgun API Key")


class MailgunProvider:
    """Mailgun provider implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = "https://api.mailgun.net"
    
    def validate_config(self) -> bool:
        """Validate provider configuration"""
        return bool(self.config.get("api_key"))
    
    async def create_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create alert/incident"""
        pass
    
    async def close_alert(self, alert_id: str) -> Dict[str, Any]:
        """Close alert/incident"""
        pass


PROVIDER_CONFIG = {
    "id": "mailgun",
    "name": "Mailgun",
    "description": "Mailgun provider for alert and incident management",
    "categories": ["email"],
    "auth_config": {
        "api_key": {
            "type": "string",
            "description": "Mailgun API Key"
        }
    },
    "base_url": "https://api.mailgun.net"
}

__all__ = ["MailgunProvider", "PROVIDER_CONFIG"]
