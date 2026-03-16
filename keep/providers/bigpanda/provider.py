"""
Pushover Provider for Keep

This provider sends alerts to Pushover, a simple notification service for mobile devices.
"""

import logging
from typing import Optional
import requests

from keep.contextmanager.contextmanager import ContextManager
from keep.providers.base.base_provider import BaseProvider
from keep.providers.models.provider_config import ProviderConfig, ProviderScope

logger = logging.getLogger(__name__)

class PushoverProvider(BaseProvider):
    """Send alerts to Pushover for mobile notifications."""

    PROVIDER_DISPLAY_NAME = "Pushover"
    PROVIDER_TAGS = ['alert', 'incident', 'ai', 'it-ops', 'correlation']
    PROVIDER_DESCRIPTION = "BigPanda provider for AI-powered incident correlation and IT operations."

    PROVIDER_SCOPES = [
        ProviderScope(
            name="authenticated",
            description="Pushover API token and user key are configured",
            mandatory=True,
            alias="Configuration",
        ),
    ]

    def __init__(
        self,
        context_manager: ContextManager,
        provider_id: str,
        config: ProviderConfig,
    ):
        super().__init__(context_manager, provider_id, config)
        self.api_token = None
        self.user_key = None

    def dispose(self):
        """Dispose the provider."""
        pass

    def validate_config(self):
        """Validate provider configuration."""
        self.authentication_config.validate("api_token")
        self.authentication_config.validate("user_key")
        self.api_token = self.authentication_config.get("api_token")
        self.user_key = self.authentication_config.get("user_key")

    def validate_scopes(self):
        """Validate provider scopes."""
        try:
            # Test Pushover API credentials
            response = requests.post(
                "https://api.pushover.net/1/messages.json",
                data={
                    "token": self.api_token,
                    "user": self.user_key,
                    "message": "Keep validation test"
                },
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Pushover validation failed: {e}")
            return False

    def _notify(
        self,
        message: str,
        title: Optional[str] = "Keep Alert",
        priority: int = 0,
        sound: Optional[str] = None,
        device: Optional[str] = None,
        url: Optional[str] = None,
        url_title: Optional[str] = None,
        **kwargs
    ):
        """
        Send alert to Pushover.

        Args:
            message: Alert message
            title: Alert title (default: "Keep Alert")
            priority: Message priority (-2 to 2, default: 0)
            sound: Notification sound
            device: Target device name
            url: Supplementary URL
            url_title: URL title
            **kwargs: Additional parameters
        """
        # Build Pushover API payload
        payload = {
            "token": self.api_token,
            "user": self.user_key,
            "message": message,
            "title": title,
            "priority": priority,
        }

        # Add optional fields
        if sound:
            payload["sound"] = sound
        if device:
            payload["device"] = device
        if url:
            payload["url"] = url
        if url_title:
            payload["url_title"] = url_title

        # Add any additional fields
        payload.update(kwargs)

        try:
            response = requests.post(
                "https://api.pushover.net/1/messages.json",
                data=payload,
                timeout=30
            )
            response.raise_for_status()
            logger.info(f"Pushover notification sent successfully: {title}")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to send Pushover notification: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise

    def notify(
        self,
        message: str,
        title: Optional[str] = "Keep Alert",
        priority: int = 0,
        sound: Optional[str] = None,
        device: Optional[str] = None,
        **kwargs
    ):
        """
        Send notification to Pushover.

        Args:
            message: Notification message
            title: Notification title
            priority: Message priority
            sound: Notification sound
            device: Target device
            **kwargs: Additional parameters
        """
        return self._notify(
            message=message,
            title=title,
            priority=priority,
            sound=sound,
            device=device,
            **kwargs
        )

    def query(self, **kwargs):
        """Query is not supported for Pushover provider."""
        raise NotImplementedError("Query operation is not supported for Pushover provider")
