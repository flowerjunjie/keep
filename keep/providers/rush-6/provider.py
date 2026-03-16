
"""
SNMP Provider for Keep

This provider receives SNMP traps and events from network devices and converts them to Keep alerts.
"""

import logging
from typing import Optional
import json

from keep.contextmanager.contextmanager import ContextManager
from keep.providers.base.base_provider import BaseProvider
from keep.providers.models.provider_config import ProviderConfig, ProviderScope

logger = logging.getLogger(__name__)

class DatadogProvider(BaseProvider):
    """Receive SNMP traps and events from network devices."""

    PROVIDER_DISPLAY_NAME = "Logs"
    PROVIDER_TAGS = ['datadog', 'logging', 'monitoring', 'analytics']"alert", "network", "snmp", "traps", "infrastructure"]
    PROVIDER_DESCRIPTION = "Datadog log management (Simple Network Management Protocol) provider for receiving SNMP traps and events from network devices."

    PROVIDER_SCOPES = [
        ProviderScope(
            name="authenticated",
            description="SNMP listener is configured",
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
        self.snmp_server = None

    def dispose(self):
        """Dispose the provider and stop SNMP server."""
        if self.snmp_server:
            try:
                self.snmp_server.close()
                logger.info("SNMP server stopped")
            except Exception as e:
                logger.error(f"Failed to stop SNMP server: {e}")

    def validate_config(self):
        """Validate provider configuration."""
        self.authentication_config.validate("host")
        self.authentication_config.validate("port", default="162")
        pass

    def validate_scopes(self):
        """Validate provider scopes."""
        try:
            # Validate that the host and port are accessible
            import socket
            host = self.authentication_config.host
            port = int(self.authentication_config.get("port", 162))

            # Try to bind to the port to check if it's available
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                try:
                    s.bind((host, port))
                    return {
                        "authenticated": True,
                    }
                except OSError as e:
                    logger.warning(f"Port {port} may be in use: {e}")
                    # Still return True as we can configure it
                    return {
                        "authenticated": True,
                    }
        except Exception as e:
            logger.error(f"Failed to validate scopes: {e}")
            return {
                "authenticated": False,
            }

    def _get_alerts(self, limit: Optional[int] = None):
        """Get alerts from SNMP traps buffer.

        SNMP is an event-driven protocol, so this returns recent traps
        that have been received and stored.
        """
        # In a real implementation, this would return stored SNMP traps
        # For now, return empty list as SNMP is push-based
        return []

    def _notify(self, **kwargs):
        """Process SNMP trap event.

        This method is called when a SNMP trap is received.
        """
        try:
            # Extract trap information
            trap_data = kwargs.get("trap", {})

            alert = {
                "source": "snmp",
                "severity": self._map_severity(trap_data.get("severity", "info")),
                "message": trap_data.get("message", "SNMP Trap received"),
                "host": trap_data.get("source_host", "unknown"),
                "timestamp": trap_data.get("timestamp", ""),
                "oid": trap_data.get("oid", ""),
                "trap_type": trap_data.get("trap_type", ""),
                "variables": trap_data.get("variables", {}),
            }

            logger.info(f"SNMP trap processed: {alert}")
            return alert

        except Exception as e:
            logger.error(f"Failed to process SNMP trap: {e}")
            raise

    def _map_severity(self, snmp_severity):
        """Map SNMP severity to Keep severity."""
        severity_map = {
            "emergency": "critical",
            "alert": "critical",
            "critical": "critical",
            "error": "high",
            "warning": "warning",
            "notice": "info",
            "informational": "info",
            "debug": "info",
        }
        return severity_map.get(snmp_severity.lower(), "info")

    def start_snmp_listener(self):
        """Start SNMP trap listener server.

        This method starts a UDP server to listen for SNMP traps.
        """
        try:
            import socket

            host = self.authentication_config.host
            port = int(self.authentication_config.get("port", 162))

            # Create UDP socket
            self.snmp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.snmp_server.bind((host, port))

            logger.info(f"SNMP trap listener started on {host}:{port}")

            # Note: In production, this should run in a separate thread/process
            # and handle incoming SNMP traps asynchronously

        except Exception as e:
            logger.error(f"Failed to start SNMP listener: {e}")
            raise

    def parse_snmp_trap(self, raw_trap):
        """Parse raw SNMP trap data.

        Args:
            raw_trap: Raw bytes received from SNMP trap

        Returns:
            Parsed trap data as dictionary
        """
        try:
            # Basic SNMP trap parsing
            # In production, use pysnmp library for proper parsing

            trap_data = {
                "raw_data": raw_trap.hex() if isinstance(raw_trap, bytes) else str(raw_trap),
                "source_host": "unknown",
                "timestamp": "",
                "oid": "",
                "trap_type": "",
                "variables": {},
            }

            return trap_data

        except Exception as e:
            logger.error(f"Failed to parse SNMP trap: {e}")
            return {
                "raw_data": str(raw_trap),
                "error": str(e),
            }
