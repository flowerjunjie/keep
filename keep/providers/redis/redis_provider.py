"""Redis Provider"""
import requests
from typing import Dict, Any

class RedisProvider:
    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get("api_key")
        if not self.api_key:
            raise ValueError("api_key required")
    def send_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "sent"}
    def test_connection(self) -> bool:
        return True
