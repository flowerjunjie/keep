"""Confluent"""
import requests
from typing import Dict, Any

class ConfluentProvider:
    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get("api_key")
    def send(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "ok"}
