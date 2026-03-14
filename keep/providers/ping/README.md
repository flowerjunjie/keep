# Ping Provider

## 概述

Ping Provider 是 KeepHQ 的一个示例 provider，用于测试 API 连接。

## 功能

- ✅ 发送 ping 请求
- ✅ 测试 API 可达性
- ✅ 连接池和自动重试
- ✅ 完整错误处理
- ✅ 超时控制

## 配置

### 必需字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `api_url` | string | API 端点 URL |

### 可选字段

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `timeout` | int | 30 | 请求超时（秒） |
| `verify_ssl` | bool | true | 是否验证 SSL |
| `max_retries` | int | 3 | 最大重试次数 |

## 使用

### 基本使用

```python
from keep.providers.ping import PingProvider

# 初始化
provider = PingProvider({
    "api_url": "https://api.example.com/ping"
})

# 发送告警
result = provider.send_alert({
    "message": "Test alert"
})

print(result)
# {"status": "ok", "response": {...}}
```

### 测试连接

```python
if provider.test_connection():
    print("连接成功")
else:
    print("连接失败")
```

### 自定义配置

```python
provider = PingProvider({
    "api_url": "https://api.example.com/ping",
    "timeout": 60,        # 60秒超时
    "verify_ssl": False,  # 不验证 SSL
    "max_retries": 5      # 重试5次
})
```

## 错误处理

### ConnectionError

网络连接问题，包括:
- 超时
- HTTP 错误 (4xx, 5xx)
- DNS 解析失败

```python
try:
    provider.send_alert({"message": "test"})
except ConnectionError as e:
    print(f"连接错误: {e}")
```

### ValueError

配置问题，包括:
- 缺少必需字段
- 无效的配置值

```python
try:
    provider = PingProvider({})  # 缺少 api_url
except ValueError as e:
    print(f"配置错误: {e}")
```

## 性能特性

- **连接池**: 复用 HTTP 连接
- **自动重试**: 失败自动重试（最多3次）
- **超时控制**: 防止长时间等待
- **高效**: 使用 requests.Session

## 测试

运行测试:

```bash
pytest keep/providers/ping/test_ping_provider.py -v
```

运行覆盖率:

```bash
pytest keep/providers/ping/test_ping_provider.py --cov=keep.providers.ping --cov-report=html
```

## 故障排查

### 问题: 超时

**原因**: API 响应慢或网络问题

**解决**:
```python
provider = PingProvider({
    "api_url": "https://api.example.com",
    "timeout": 60  # 增加超时
})
```

### 问题: SSL 错误

**原因**: 自签名证书或 SSL 问题

**解决**:
```python
provider = PingProvider({
    "api_url": "https://api.example.com",
    "verify_ssl": False  # 跳过 SSL 验证
})
```

### 问题: 连接失败

**原因**: API 不可达

**解决**:
```python
if not provider.test_connection():
    print("API 不可达，检查 URL 和网络")
```

## 架构

PingProvider 继承自 BaseProvider，享受:

- 统一的配置验证
- 自动连接池
- 智能重试
- 标准错误处理

## 贡献

要添加新的 provider:

1. 继承 `BaseProvider`
2. 实现 `send_alert()` 和 `test_connection()`
3. 定义 `REQUIRED_FIELDS`
4. 添加完整测试
5. 编写文档

参考 PingProvider 作为示例。

## 许可

Apache License 2.0
