# Nagios Provider

Nagios monitoring provider provider for Keep.

## Configuration

```json
{
  "api_url": "https://nagios.example.com/api",
  "api_key": "your-api-key-here",
  "verify_ssl": true,
  "timeout": 30
}
```

## Features

- Get alerts from Nagios
- Create alerts in Nagios
- Update alerts in Nagios
- Delete alerts from Nagios

## Usage

```python
from keep.providers.nagios import NagiosProvider

provider = NagiosProvider(config={
    "api_url": "https://nagios.example.com/api",
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
