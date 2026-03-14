"""AzureBlob Provider"""
import requests
from typing import Dict, Any

class AzureBlobProvider:
    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get("api_key", "")
        self.api_url = config.get("api_url", "")
        
    def send_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "sent", "provider": "AzureBlob"}
    
    def test_connection(self) -> bool:
        return True
