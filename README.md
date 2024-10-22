# Geni SDK Python Wrapper

A Python SDK for interacting with the Geni.com API, providing simplified access to Geni's genealogy platform features.

## Features

- Event-driven architecture similar to the JavaScript SDK
- OAuth authentication handling
- Simple API request interface
- Status management and tracking
- Local callback server for OAuth flow
- Cookie-based token storage support
- Debug logging capabilities

## Usage

First, clone this repository:

```bash
git clone [your-repository-url]
cd [repository-name]
```

Then, in your Python code:

```python
from geni_wrapper import GeniSDK

# Initialize the SDK with your app ID
geni = GeniSDK(app_id='your_app_id_here')

# Handle authentication status changes
def on_status_change(status):
    print(f"Auth status changed to: {status}")

geni.Event.bind('auth:statusChange', on_status_change)

# Connect to Geni
def auth_callback(response):
    if response['status'] == 'authorized':
        print("Successfully connected!")
        # Make API calls here
    else:
        print("Authorization failed:", response.get('error'))

geni.connect(callback=auth_callback)
```

## Authentication

The SDK handles OAuth 2.0 authentication with Geni.com. When calling `connect()`, it will:

1. Open a browser window for user authorization
2. Start a local server to receive the OAuth callback
3. Handle the token exchange automatically
4. Store the access token for subsequent API calls

```python
# Check current authentication status
status = geni.get_status()
print(status['status'])  # 'authorized', 'unauthorized', or 'unknown'

# Logout
geni.logout()
```

## Making API Calls

Once authenticated, you can make API calls to any Geni endpoint:

```python
# GET request
response = geni.api('/profile')

# GET request with parameters
response = geni.api('/profile-101/tree_matches', {
    'names': 'John Smith',
    'birth_year': 1900
})

# POST request
response = geni.api('/profile', {
    'method': 'POST',
    'names': 'John Smith',
    'gender': 'male'
})
```

## Event System

The SDK includes an event system for handling state changes:

```python
# Subscribe to authentication status changes
def status_changed(new_status):
    print(f"Authentication status: {new_status}")

geni.Event.bind('auth:statusChange', status_changed)

# Unsubscribe from events
geni.Event.unbind('auth:statusChange', status_changed)
```

## Configuration Options

When initializing the SDK, you can specify several options:

```python
geni = GeniSDK(
    app_id='your_app_id_here',
    host='https://www.geni.com',  # Custom API host if needed
    cookies=True,  # Enable cookie storage of tokens
    logging=True   # Enable debug logging
)
```

## Error Handling

The SDK includes built-in error handling:

```python
response = geni.api('/invalid/endpoint')
if 'error' in response:
    print(f"API Error: {response['error']}")
```

## Version

Current version: 0.2.1

## Requirements

- Python 3.6+
- requests library (`pip install requests`)

## Dependencies Installation

Install the required dependencies:

```bash
pip install requests
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For bug reports and feature requests, please open an issue on GitHub.

For questions about the Geni API itself, please refer to the [Geni API Documentation](https://www.geni.com/platform/developer).