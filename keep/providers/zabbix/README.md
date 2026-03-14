# Zabbix Provider

Zabbix monitoring provider provider for Keep.

## Configuration

```json
{
  "api_url": "https://zabbix.example.com/api",
  "api_key": "your-api-key-here",
  "verify_ssl": true,
  "timeout": 30
}
```

## Features

- Get alerts from Zabbix
- Create alerts in Zabbix
- Update alerts in Zabbix
- Delete alerts from Zabbix

## Usage

```python
from keep.providers.zabbix import ZabbixProvider

provider = ZabbixProvider(config={
    "api_url": "https://zabbix.example.com/api",
    "api_key": "your-api-key"
})

# Test connection
if provider.test_connection():
    print("Connection successful!")

# Get alerts
alerts = provider.get_alerts()
```

## Requirements

- Python 3.8+
- requests
