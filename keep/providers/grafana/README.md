# Grafana Provider

Grafana analytics provider provider for Keep.

## Configuration

```json
{
  "api_url": "https://grafana.example.com/api",
  "api_key": "your-api-key-here",
  "verify_ssl": true,
  "timeout": 30
}
```

## Features

- Get alerts from Grafana
- Create alerts in Grafana
- Update alerts in Grafana
- Delete alerts from Grafana

## Usage

```python
from keep.providers.grafana import GrafanaProvider

provider = GrafanaProvider(config={
    "api_url": "https://grafana.example.com/api",
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
