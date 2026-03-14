# Prometheus Provider

Prometheus monitoring provider provider for Keep.

## Configuration

```json
{
  "api_url": "https://prometheus.example.com/api",
  "api_key": "your-api-key-here",
  "verify_ssl": true,
  "timeout": 30
}
```

## Features

- Get alerts from Prometheus
- Create alerts in Prometheus
- Update alerts in Prometheus
- Delete alerts from Prometheus

## Usage

```python
from keep.providers.prometheus import PrometheusProvider

provider = PrometheusProvider(config={
    "api_url": "https://prometheus.example.com/api",
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
