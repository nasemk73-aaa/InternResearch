#!/usr/bin/env python3
# Copyright (C) 2026 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

import json
import time
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from ..authenticate import (
    _find_available_port,
    _load_cached_token,
    _OAuthCallbackHandler,
    _OAuthResult,
    _save_token,
    get_cached_bearer_token,
)


class TestTokenCache:
    def test_save_and_load(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        cache_file = tmp_path / "token.json"
        monkeypatch.setenv("CRASH_REPORTING_TOKEN_CACHE", str(cache_file))

        _save_token("test-token-123", 3600)

        data = _load_cached_token()
        assert data is not None
        assert data["token"] == "test-token-123"
        assert data["expires_at"] > time.time()

    def test_load_expired_token(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        cache_file = tmp_path / "token.json"
        monkeypatch.setenv("CRASH_REPORTING_TOKEN_CACHE", str(cache_file))

        # Write an already-expired token
        data = {
            "token": "expired-token",
            "expires_at": int(time.time()) - 100,
            "issued_at": int(time.time()) - 3700,
        }
        cache_file.write_text(json.dumps(data))

        result = _load_cached_token()
        assert result is None

    def test_load_missing_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        cache_file = tmp_path / "nonexistent" / "token.json"
        monkeypatch.setenv("CRASH_REPORTING_TOKEN_CACHE", str(cache_file))

        result = _load_cached_token()
        assert result is None

    def test_load_invalid_json(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        cache_file = tmp_path / "token.json"
        cache_file.write_text("not json")
        monkeypatch.setenv("CRASH_REPORTING_TOKEN_CACHE", str(cache_file))

        result = _load_cached_token()
        assert result is None

    def test_get_cached_bearer_token_valid(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cache_file = tmp_path / "token.json"
        monkeypatch.setenv("CRASH_REPORTING_TOKEN_CACHE", str(cache_file))

        _save_token("my-bearer", 3600)

        result = get_cached_bearer_token()
        assert result == "my-bearer"

    def test_get_cached_bearer_token_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cache_file = tmp_path / "nonexistent.json"
        monkeypatch.setenv("CRASH_REPORTING_TOKEN_CACHE", str(cache_file))

        result = get_cached_bearer_token()
        assert result is None

    def test_save_creates_parent_dirs(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cache_file = tmp_path / "sub" / "dir" / "token.json"
        monkeypatch.setenv("CRASH_REPORTING_TOKEN_CACHE", str(cache_file))

        _save_token("test-token", 3600)
        assert cache_file.is_file()

    def test_save_sets_permissions(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        cache_file = tmp_path / "token.json"
        monkeypatch.setenv("CRASH_REPORTING_TOKEN_CACHE", str(cache_file))

        _save_token("secret-token", 3600)
        assert oct(cache_file.stat().st_mode & 0o777) == "0o600"

    def test_token_near_expiry_still_valid(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Token with >60s remaining should still be returned."""
        cache_file = tmp_path / "token.json"
        monkeypatch.setenv("CRASH_REPORTING_TOKEN_CACHE", str(cache_file))

        # expires_at is 65 seconds from now — within the 60s buffer, so still valid
        data = {
            "token": "almost-expired",
            "expires_at": int(time.time()) + 65,
            "issued_at": int(time.time()) - 3535,
        }
        cache_file.write_text(json.dumps(data))

        result = _load_cached_token()
        assert result is not None
        assert result["token"] == "almost-expired"

    def test_token_within_60s_buffer_expired(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Token with <=60s remaining should be treated as expired (60s safety buffer)."""
        cache_file = tmp_path / "token.json"
        monkeypatch.setenv("CRASH_REPORTING_TOKEN_CACHE", str(cache_file))

        data = {
            "token": "buffer-expired",
            "expires_at": int(time.time()) + 55,
            "issued_at": int(time.time()) - 3545,
        }
        cache_file.write_text(json.dumps(data))

        result = _load_cached_token()
        assert result is None


class TestFindAvailablePort:
    def test_returns_port_in_range(self) -> None:
        port = _find_available_port()
        assert 18520 <= port < 18530


def _simulate_callback(handler_class: type, oauth_result: _OAuthResult, path: str) -> None:
    """Simulate an HTTP GET request to the callback handler."""
    handler: _OAuthCallbackHandler = object.__new__(handler_class)
    handler.server = MagicMock()
    handler.server.oauth_result = oauth_result
    handler.path = path
    handler.wfile = BytesIO()
    handler.send_response = MagicMock()  # type: ignore[method-assign]
    handler.send_header = MagicMock()  # type: ignore[method-assign]
    handler.end_headers = MagicMock()  # type: ignore[method-assign]
    handler.do_GET()


class TestOAuthCallbackHandler:
    def test_extracts_token_and_state(self) -> None:
        result = _OAuthResult(expected_state="mystate")
        _simulate_callback(
            _OAuthCallbackHandler,
            result,
            "/?token=jwt123&state=mystate&expires_in=7200",
        )
        assert result.token == "jwt123"
        assert result.expires_in == 7200
        assert result.auth_error is None

    def test_state_mismatch(self) -> None:
        result = _OAuthResult(expected_state="expected")
        _simulate_callback(
            _OAuthCallbackHandler,
            result,
            "/?token=jwt123&state=wrong",
        )
        assert result.token is None
        assert result.auth_error == "State mismatch (possible CSRF)"

    def test_error_param(self) -> None:
        result = _OAuthResult(expected_state="mystate")
        _simulate_callback(
            _OAuthCallbackHandler,
            result,
            "/?error=access_denied&state=mystate",
        )
        assert result.token is None
        assert result.auth_error == "access_denied"

    def test_missing_token(self) -> None:
        result = _OAuthResult(expected_state="mystate")
        _simulate_callback(
            _OAuthCallbackHandler,
            result,
            "/?state=mystate",
        )
        assert result.token is None
        assert result.auth_error == "No token received"

    def test_invalid_expires_in_defaults_to_3600(self) -> None:
        result = _OAuthResult(expected_state="mystate")
        _simulate_callback(
            _OAuthCallbackHandler,
            result,
            "/?token=jwt123&state=mystate&expires_in=notanumber",
        )
        assert result.token == "jwt123"
        assert result.expires_in == 3600
