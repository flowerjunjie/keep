
"""
Base Provider - 所有 providers 的抽象基类

这个基类定义了所有 providers 必须实现的接口，
确保一致性和可维护性。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from dataclasses import dataclass
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


@dataclass
class ProviderConfig:
    """Provider 配置"""
    api_key: str
    api_url: str
    timeout: int = 30
    verify_ssl: bool = True
    max_retries: int = 3


class BaseProvider(ABC):
    """
    所有 providers 的抽象基类

    提供通用功能:
    - 配置验证
    - HTTP 连接池
    - 自动重试
    - 错误处理
    """

    # 每个 provider 必须定义这些
    REQUIRED_FIELDS: List[str] = []
    OPTIONAL_FIELDS: Dict[str, Any] = {}

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 provider

        Args:
            config: 配置字典

        Raises:
            ValueError: 配置无效
            ConnectionError: 连接失败
        """
        self.config = self._validate_config(config)
        self.session = self._create_session()

    def _validate_config(self, config: Dict[str, Any]) -> ProviderConfig:
        """
        验证配置

        Args:
            config: 原始配置

        Returns:
            验证后的配置对象

        Raises:
            ValueError: 缺少必需字段
        """
        # 检查必需字段
        missing = [f for f in self.REQUIRED_FIELDS if f not in config]
        if missing:
            raise ValueError(
                f"{self.__class__.__name__}: "
                f"Missing required fields: {missing}"
            )

        # 合并可选字段
        full_config = {**self.OPTIONAL_FIELDS, **config}

        return ProviderConfig(
            api_key=full_config.get("api_key"),
            api_url=full_config.get("api_url"),
            timeout=full_config.get("timeout", 30),
            verify_ssl=full_config.get("verify_ssl", True),
            max_retries=full_config.get("max_retries", 3)
        )

    def _create_session(self) -> requests.Session:
        """
        创建带连接池和重试的 HTTP session

        Returns:
            配置好的 session
        """
        session = requests.Session()

        # 配置重试策略
        retry = Retry(
            total=self.config.max_retries,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )

        # 配置连接池
        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=retry
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    @abstractmethod
    def send_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送告警

        Args:
            alert: 告警数据

        Returns:
            发送结果

        Raises:
            ConnectionError: 网络错误
            ValueError: 数据格式错误
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """
        测试连接

        Returns:
            连接是否成功
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(url={self.config.api_url})"
