# Twilio Provider

Twilio integration for Keep.

## Configuration

```json
{
  "api_key": "your-twilio-api-key",
  "api_url": "https://api.twilio.com",
  "timeout": 30
}
```

## Features

- Send alerts to Twilio
- Test connection
- Error handling

## Usage

```python
from keep.providers.twilio import TwilioProvider

provider = TwilioProvider(config={"api_key": "your-key"})

# Test
if provider.test_connection():
    print("Connected!")

# Send alert
provider.send_alert({"message": "Test alert"})
```

## Requirements

- Python 3.8+
- requests
