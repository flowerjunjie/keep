"""
SMTP Provider for Keep
Category: email
Base URL: smtp://localhost
"""

from typing import Any, Dict
from pydantic import BaseModel, Field


class SMTPConfig(BaseModel):
    """SMTP configuration"""
    api_key: str = Field(..., description="SMTP API Key")


class SMTPProvider:
    """SMTP provider implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = "smtp://localhost"
    
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
    "id": "smtp",
    "name": "SMTP",
    "description": "SMTP provider for alert and incident management",
    "categories": ["email"],
    "auth_config": {
        "api_key": {
            "type": "string",
            "description": "SMTP API Key"
        }
    },
    "base_url": "smtp://localhost"
}

__all__ = ["SMTPProvider", "PROVIDER_CONFIG"]
