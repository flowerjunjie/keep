# Opsgenie Provider

Opsgenie integration for Keep.

## Configuration

```json
{
  "api_key": "your-opsgenie-api-key",
  "api_url": "https://api.opsgenie.com",
  "timeout": 30
}
```

## Features

- Send alerts to Opsgenie
- Test connection
- Error handling

## Usage

```python
from keep.providers.opsgenie import OpsgenieProvider

provider = OpsgenieProvider(config={"api_key": "your-key"})

# Test
if provider.test_connection():
    print("Connected!")

# Send alert
provider.send_alert({"message": "Test alert"})
```

## Requirements

- Python 3.8+
- requests
