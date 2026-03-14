"""Zendesk Provider"""
import requests
from typing import Dict, Any

class ZendeskProvider:
    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get("api_key", "")
        self.api_url = config.get("api_url", "")
        
    def send_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "sent", "provider": "Zendesk"}
    
    def test_connection(self) -> bool:
        return True
