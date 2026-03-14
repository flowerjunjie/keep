
"""
Ping Provider 测试套件

完整的单元测试、集成测试和边界测试。
"""

import pytest
from keep.providers.ping.ping_provider import PingProvider


class TestPingProvider:
    """PingProvider 测试"""

    def test_init_with_valid_config(self):
        """测试: 有效配置初始化"""
        config = {
            "api_url": "https://httpbin.org/status/200"
        }
        provider = PingProvider(config)

        assert provider.config.api_url == "https://httpbin.org/status/200"
        assert provider.config.timeout == 30
        assert provider.config.verify_ssl == True

    def test_init_with_custom_config(self):
        """测试: 自定义配置"""
        config = {
            "api_url": "https://httpbin.org/status/200",
            "timeout": 60,
            "verify_ssl": False
        }
        provider = PingProvider(config)

        assert provider.config.timeout == 60
        assert provider.config.verify_ssl == False

    def test_init_missing_api_url(self):
        """测试: 缺少 api_url 抛出异常"""
        config = {}

        with pytest.raises(ValueError, match="Missing required fields"):
            PingProvider(config)

    def test_send_alert_success(self):
        """测试: 成功发送告警"""
        config = {"api_url": "https://httpbin.org/status/200"}
        provider = PingProvider(config)

        result = provider.send_alert({"message": "test"})

        assert result["status"] == "ok"
        assert "response" in result
        assert result["response"]["status_code"] == 200

    def test_send_alert_404(self):
        """测试: 404 错误"""
        config = {"api_url": "https://httpbin.org/status/404"}
        provider = PingProvider(config)

        with pytest.raises(ConnectionError, match="HTTP error: 404"):
            provider.send_alert({"message": "test"})

    def test_send_alert_timeout(self):
        """测试: 超时错误"""
        config = {
            "api_url": "https://httpbin.org/delay/10",
            "timeout": 1  # 1秒超时
        }
        provider = PingProvider(config)

        with pytest.raises(ConnectionError, match="timeout"):
            provider.send_alert({"message": "test"})

    def test_connection_success(self):
        """测试: 连接成功"""
        config = {"api_url": "https://httpbin.org/status/200"}
        provider = PingProvider(config)

        assert provider.test_connection() == True

    def test_connection_failure(self):
        """测试: 连接失败"""
        config = {"api_url": "https://invalid-url-that-does-not-exist.com"}
        provider = PingProvider(config)

        assert provider.test_connection() == False

    def test_repr(self):
        """测试: 字符串表示"""
        config = {"api_url": "https://example.com"}
        provider = PingProvider(config)

        assert "PingProvider" in str(provider)
        assert "https://example.com" in str(provider)
