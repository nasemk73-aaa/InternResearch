#!/usr/bin/env python3
# Copyright (C) 2026 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

"""Authenticate with crash.checkmk.com and cache a bearer token.

Usage:
    PYTHONPATH=.github/skills python3 -m crash_report.authenticate [--force]

This script:
1. Opens a browser pointing to crash.checkmk.com's authentication endpoint
2. The server handles Google Sign-In and redirects back with a JWT
3. A local HTTP server captures the JWT from the redirect
4. Caches the bearer token locally for use by fetch_crash_data.py

Options:
    --force    Force re-authentication even if a valid token is cached.

Environment:
    CRASH_REPORTING_TOKEN_CACHE           - Override token cache path
                                            (default: ~/.cache/cmk-crash-reporting/token.json)
"""

import dataclasses
import http.server
import json
import os
import secrets
import socket
import sys
import threading
import time
import urllib.parse
import webbrowser
from pathlib import Path
from typing import Any

BASE_URL = os.environ.get("CRASH_REPORTING_URL", "https://crash.checkmk.com")
TOKEN_ENDPOINT = f"{BASE_URL}/gui/api/v1/statsapi/auth/token"

DEFAULT_CACHE_DIR = Path.home() / ".cache" / "cmk-crash-reporting"
DEFAULT_CACHE_FILE = DEFAULT_CACHE_DIR / "token.json"

# Localhost callback port range
CALLBACK_PORT_START = 18520
CALLBACK_PORT_END = 18530


def _get_cache_path() -> Path:
    return Path(os.environ.get("CRASH_REPORTING_TOKEN_CACHE", str(DEFAULT_CACHE_FILE)))


def _load_cached_token() -> dict[str, Any] | None:
    """Load and validate the cached bearer token."""
    cache_path = _get_cache_path()
    if not cache_path.is_file():
        return None

    try:
        data = json.loads(cache_path.read_text())
    except (json.JSONDecodeError, OSError):
        return None

    # Check expiry (with 60s buffer)
    expires_at = data.get("expires_at", 0)
    if time.time() >= expires_at - 60:
        return None

    return dict(data)  # explicit dict to satisfy mypy (json.loads returns Any)


def _save_token(token: str, expires_in: int) -> None:
    """Cache the bearer token to disk."""
    cache_path = _get_cache_path()
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    now = int(time.time())
    data = {
        "token": token,
        "expires_at": now + expires_in,
        "issued_at": now,
    }
    cache_path.write_text(json.dumps(data, indent=2))
    cache_path.chmod(0o600)


def get_cached_bearer_token() -> str | None:
    """Return a valid cached bearer token, or None if unavailable/expired.

    This is the main entry point for fetch_crash_data.py to get a token.
    """
    data = _load_cached_token()
    if data:
        return str(data["token"])
    return None


@dataclasses.dataclass
class _OAuthResult:
    """Mutable container for OAuth callback results, stored on the server instance."""

    expected_state: str = ""
    token: str | None = None
    expires_in: int = 3600
    auth_error: str | None = None


class _OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler that captures the JWT token from the server redirect."""

    server: "_OAuthHTTPServer"  # type: ignore[mutable-override]

    def do_GET(self) -> None:
        result = self.server.oauth_result
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        error = params.get("error", [None])[0]
        if error:
            result.auth_error = error
            self._respond("Authentication failed. You can close this window.")
            return

        state = params.get("state", [None])[0]
        if state != result.expected_state:
            result.auth_error = "State mismatch (possible CSRF)"
            self._respond("State mismatch error. You can close this window.")
            return

        token = params.get("token", [None])[0]
        if token:
            result.token = token
            expires_in_str = params.get("expires_in", ["3600"])[0]
            try:
                result.expires_in = int(expires_in_str)
            except ValueError:
                result.expires_in = 3600
            self._respond(
                "Authentication successful! You can close this window and return to the terminal."
            )
        else:
            result.auth_error = "No token received"
            self._respond("No token received. You can close this window.")

    def _respond(self, message: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        html = f"<html><body><h2>{message}</h2></body></html>"
        self.wfile.write(html.encode())

    def log_message(self, _format: str, *args: Any) -> None:
        pass  # Suppress HTTP server logs


class _OAuthHTTPServer(http.server.HTTPServer):
    """HTTPServer subclass that carries OAuth result state."""

    def __init__(self, address: tuple[str, int], oauth_result: _OAuthResult) -> None:
        super().__init__(address, _OAuthCallbackHandler)
        self.oauth_result = oauth_result


def _find_available_port() -> int:
    """Find an available port for the callback server."""
    for port in range(CALLBACK_PORT_START, CALLBACK_PORT_END):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError(f"No available port in range {CALLBACK_PORT_START}-{CALLBACK_PORT_END}")


def authenticate(force: bool = False) -> str:
    """Run the authentication flow and return a bearer token.

    Opens the browser to crash.checkmk.com's authentication endpoint, which
    handles Google Sign-In and redirects back to a local server with a JWT.

    If a valid cached token exists and force=False, returns it immediately.

    Args:
        force: Force re-authentication even if a valid token is cached.
    """
    if not force:
        cached = get_cached_bearer_token()
        if cached:
            print("Using cached bearer token (still valid).")
            return cached

    port = _find_available_port()
    redirect_uri = f"http://127.0.0.1:{port}"

    # Generate CSRF state and result container
    oauth_result = _OAuthResult(expected_state=secrets.token_urlsafe(32))

    # Build server auth URL — the server handles Google OAuth
    auth_params = urllib.parse.urlencode(
        {
            "redirect_uri": redirect_uri,
            "state": oauth_result.expected_state,
        }
    )
    auth_url = f"{TOKEN_ENDPOINT}?{auth_params}"

    # Start local callback server
    server = _OAuthHTTPServer(("127.0.0.1", port), oauth_result)
    server_thread = threading.Thread(target=server.handle_request, daemon=True)
    server_thread.start()

    print("Opening browser for authentication...")
    print(f"If the browser doesn't open, visit:\n  {auth_url}\n")
    webbrowser.open(auth_url)

    # Wait for callback
    server_thread.join(timeout=120)
    server.server_close()

    if oauth_result.auth_error:
        sys.stderr.write(f"Authentication error: {oauth_result.auth_error}\n")
        sys.exit(1)

    if not oauth_result.token:
        sys.stderr.write("Authentication timed out (120s).\n")
        sys.exit(1)

    _save_token(oauth_result.token, oauth_result.expires_in)
    print(
        f"Authenticated successfully. Token cached "
        f"(expires in {oauth_result.expires_in // 60} minutes)."
    )
    return oauth_result.token


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Authenticate with crash.checkmk.com")
    parser.add_argument("--force", action="store_true", help="Force re-authentication")
    args = parser.parse_args()
    authenticate(force=args.force)


if __name__ == "__main__":
    main()
