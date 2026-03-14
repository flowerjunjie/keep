# Slack Provider

Slack integration for Keep.

## Configuration

```json
{
  "api_key": "your-slack-api-key",
  "api_url": "https://api.slack.com",
  "timeout": 30
}
```

## Features

- Send alerts to Slack
- Test connection
- Error handling

## Usage

```python
from keep.providers.slack import SlackProvider

provider = SlackProvider(config={"api_key": "your-key"})

# Test
if provider.test_connection():
    print("Connected!")

# Send alert
provider.send_alert({"message": "Test alert"})
```

## Requirements

- Python 3.8+
- requests
