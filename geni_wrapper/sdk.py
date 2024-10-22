import requests
import json
import time
import random
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from typing import Optional, Dict, Any, Callable


class GeniEvent:
    """Event handling system similar to the JavaScript SDK"""

    def __init__(self):
        self._events = {}

    def bind(self, event: str, callback: Callable) -> None:
        """Subscribe to an event"""
        if event not in self._events:
            self._events[event] = []
        self._events[event].append(callback)

    def unbind(self, event: str, callback: Optional[Callable] = None) -> None:
        """Unsubscribe from an event"""
        if event not in self._events:
            return

        if callback is None:
            del self._events[event]
        else:
            self._events[event].remove(callback)

    def trigger(self, event: str, *args, **kwargs) -> None:
        """Trigger an event"""
        if event not in self._events:
            return

        for callback in self._events[event]:
            callback(*args, **kwargs)


class GeniSDK:
    VERSION = '0.2.1'

    def __init__(self, app_id: Optional[str] = None, host: str = 'https://www.geni.com',
                 cookies: bool = False, logging: bool = False):
        """
        Initialize the Geni SDK

        Args:
            app_id: Your Geni application key
            host: API host URL (default: https://www.geni.com)
            cookies: Enable cookie storage of tokens
            logging: Enable debug logging
        """
        self._app_id = app_id
        self._host = host
        self._cookies = cookies
        self._logging = logging
        self._access_token = None
        self._status = 'unknown'

        self._urls = {
            'api': '/api',
            'connect': '/oauth/authorize',
            'disconnect': '/oauth/deauthorize',
            'logout': '/oauth/logout'
        }

        # Initialize event system
        self.Event = GeniEvent()

        if not app_id:
            self._log("Geni Python SDK requires an Application ID")
            raise ValueError("Geni Python SDK requires an Application ID")

    def _log(self, *args) -> None:
        """Log debug messages if logging is enabled"""
        if self._logging:
            print("[Geni SDK]", *args)

    def _set_status(self, status: str) -> None:
        """Update authentication status and trigger event if changed"""
        if self._status != status:
            self._status = status
            self.Event.trigger('auth:statusChange', status)

    def get_status(self, callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Get current authentication status

        Returns one of three status types:
        - "authorized" - user is logged in and has authorized the app
        - "unauthorized" - user is logged in but hasn't authorized the app
        - "unknown" - user is logged out
        """
        response = {
            'status': 'unknown',
            'access_token': None
        }

        if self._access_token:
            # Verify token is still valid with a test API call
            test_response = self.api('/user')
            if not test_response.get('error'):
                response['status'] = 'authorized'
                response['access_token'] = self._access_token
            else:
                self._access_token = None

        self._set_status(response['status'])

        if callback:
            callback(response)
        return response

    def connect(self, callback: Optional[Callable] = None) -> None:
        """
        Authenticate user and get access token via OAuth popup

        Should only be called in response to a user action (e.g., button click)
        to avoid popup blocking.
        """
        if not self._app_id:
            raise ValueError("connect() called without an app id")

        if self._access_token:
            self._log("connect() called when user is already connected")
            if callback:
                callback({'status': 'authorized', 'access_token': self._access_token})
            return

        # Setup local server to receive OAuth callback
        class OAuthHandler(BaseHTTPRequestHandler):
            def do_get(self):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                query = parse_qs(urlparse(self.path).query)
                if 'access_token' in query:
                    self.server.oauth_response = {
                        'status': 'authorized',
                        'access_token': query['access_token'][0]
                    }
                else:
                    self.server.oauth_response = {
                        'status': 'unknown',
                        'error': 'Authorization failed or was cancelled'
                    }

                self.wfile.write(b"<html><body><script>window.close()</script></body></html>")

        server = HTTPServer(('localhost', 0), OAuthHandler)
        port = server.server_port

        # Open browser for authorization
        params = {
            'response_type': 'token',
            'client_id': self._app_id,
            'redirect_uri': f'http://localhost:{port}',
            'display': 'popup'
        }

        auth_url = f"{self._host}{self._urls['connect']}?" + '&'.join(f"{k}={v}" for k, v in params.items())
        webbrowser.open(auth_url)

        # Wait for callback
        server.handle_request()
        response = getattr(server, 'oauth_response', {'status': 'unknown'})

        if response['status'] == 'authorized':
            self._access_token = response['access_token']
            if self._cookies:
                # Implementation of cookie storage would go here
                pass

        self._set_status(response['status'])

        if callback:
            callback(response)

    def logout(self, callback: Optional[Callable] = None) -> None:
        """Log the user out of Geni"""
        if not self._app_id:
            raise ValueError("logout() called without an app id")

        url = f"{self._host}{self._urls['logout']}"
        params = {'client_id': self._app_id}
        if self._access_token:
            params['access_token'] = self._access_token

        try:
            requests.get(url, params=params)
        finally:
            self._access_token = None
            self._set_status('unknown')

            if callback:
                callback()

    def api(self, path: str, params: Optional[Dict] = None,
            callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Make an API call to Geni servers

        Args:
            path: API endpoint path (e.g., '/profile-101/tree_matches')
            params: Optional parameters including 'method' for POST requests
            callback: Optional callback function
        """
        if not params:
            params = {}

        method = params.pop('method', 'GET').upper()

        if self._access_token:
            params['access_token'] = self._access_token

        url = f"{self._host}{self._urls['api']}/{path.lstrip('/')}"

        try:
            response = requests.request(method, url, params=params if method == 'GET' else None,
                                        json=params if method != 'GET' else None)
            data = response.json()

            if 'error' in data:
                self._log("API error:", data['error'])
                if data.get('error', {}).get('type') == 'OAuthException':
                    self._access_token = None
                    self._set_status('unauthorized')

            if callback:
                callback(data)
            return data

        except Exception as e:
            error = {'error': str(e)}
            if callback:
                callback(error)
            return error


# Create global instance for easier access
Geni = GeniSDK