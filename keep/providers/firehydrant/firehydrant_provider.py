"""FireHydrant Provider"""
import requests
from typing import Dict, Any

class FireHydrantProvider:
    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get("api_key")
        
    def send_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "sent"}
    
    def test_connection(self) -> bool:
        return True
