# Sendgrid Provider

Sendgrid integration for Keep.

## Configuration

```json
{
  "api_key": "your-sendgrid-api-key",
  "api_url": "https://api.sendgrid.com",
  "timeout": 30
}
```

## Features

- Send alerts to Sendgrid
- Test connection
- Error handling

## Usage

```python
from keep.providers.sendgrid import SendgridProvider

provider = SendgridProvider(config={"api_key": "your-key"})

# Test
if provider.test_connection():
    print("Connected!")

# Send alert
provider.send_alert({"message": "Test alert"})
```

## Requirements

- Python 3.8+
- requests
