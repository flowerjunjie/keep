"""
Sendgrid Provider for Keep
Category: email
Base URL: https://api.sendgrid.com
"""

from typing import Any, Dict
from pydantic import BaseModel, Field


class SendgridConfig(BaseModel):
    """Sendgrid configuration"""
    api_key: str = Field(..., description="Sendgrid API Key")


class SendgridProvider:
    """Sendgrid provider implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = "https://api.sendgrid.com"
    
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
    "id": "sendgrid",
    "name": "Sendgrid",
    "description": "Sendgrid provider for alert and incident management",
    "categories": ["email"],
    "auth_config": {
        "api_key": {
            "type": "string",
            "description": "Sendgrid API Key"
        }
    },
    "base_url": "https://api.sendgrid.com"
}

__all__ = ["SendgridProvider", "PROVIDER_CONFIG"]
