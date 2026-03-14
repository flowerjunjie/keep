
"""
Ping Provider - 示例高质量 Provider

这个 provider 展示了如何继承 BaseProvider
并实现所有必需的方法。
"""

from typing import Dict, Any
from ..base.BaseProvider import BaseProvider


class PingProvider(BaseProvider):
    """
    Ping Provider - 用于测试连接

    这是最简单的 provider 实现，展示了基本模式。
    """

    REQUIRED_FIELDS = ["api_url"]
    OPTIONAL_FIELDS = {"timeout": 30, "verify_ssl": True}

    def send_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送 ping 告警

        Args:
            alert: {"message": "ping message"}

        Returns:
            {"status": "ok", "response": {...}}

        Raises:
            ConnectionError: 网络错误
        """
        try:
            response = self.session.get(
                self.config.api_url,
                timeout=self.config.timeout
            )
            response.raise_for_status()

            return {
                "status": "ok",
                "response": {
                    "status_code": response.status_code,
                    "content": response.text[:100]
                }
            }

        except requests.Timeout:
            raise ConnectionError(
                f"{self.__class__.__name__}: "
                f"Request timeout after {self.config.timeout}s"
            )

        except requests.HTTPError as e:
            raise ConnectionError(
                f"{self.__class__.__name__}: "
                f"HTTP error: {e.response.status_code}"
            )

    def test_connection(self) -> bool:
        """
        测试连接

        Returns:
            连接是否成功
        """
        try:
            response = self.session.get(
                self.config.api_url,
                timeout=5  # 短超时
            )
            return response.status_code == 200
        except Exception:
            return False
