# Mailgun Provider

Mailgun integration for Keep.

## Configuration

```json
{
  "api_key": "your-mailgun-api-key",
  "api_url": "https://api.mailgun.com",
  "timeout": 30
}
```

## Features

- Send alerts to Mailgun
- Test connection
- Error handling

## Usage

```python
from keep.providers.mailgun import MailgunProvider

provider = MailgunProvider(config={"api_key": "your-key"})

# Test
if provider.test_connection():
    print("Connected!")

# Send alert
provider.send_alert({"message": "Test alert"})
```

## Requirements

- Python 3.8+
- requests
