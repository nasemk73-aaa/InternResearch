#!/usr/bin/env python3
# Copyright (C) 2026 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from ..fetch_crash_data import (
    _load_local_crash,
    ApiError,
    format_traceback,
    parse_date,
)


class TestParseDate:
    def test_relative_days(self) -> None:
        result = parse_date("30d")
        expected = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        assert result == expected

    def test_relative_one_day(self) -> None:
        result = parse_date("1d")
        expected = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        assert result == expected

    def test_iso_date_passthrough(self) -> None:
        result = parse_date("2025-01-15")
        assert result == "2025-01-15"

    def test_iso_date_with_time_passthrough(self) -> None:
        result = parse_date("2025-01-15T10:30:00")
        assert result == "2025-01-15T10:30:00"


class TestFormatTraceback:
    def test_four_element_frames(self) -> None:
        tb = [
            ["cmk/gui/views.py", "42", "render_view", "self.page.render()"],
            ["cmk/gui/page.py", "100", "render", "return template.output()"],
        ]
        result = format_traceback(tb)
        assert 'File "cmk/gui/views.py", line 42, in render_view' in result
        assert "    self.page.render()" in result
        assert 'File "cmk/gui/page.py", line 100, in render' in result

    def test_three_element_frames(self) -> None:
        tb = [["cmk/gui/views.py", "42", "render_view"]]
        result = format_traceback(tb)
        assert 'File "cmk/gui/views.py", line 42, in render_view' in result

    def test_empty_text_in_frame(self) -> None:
        tb = [["cmk/gui/views.py", "42", "render_view", ""]]
        result = format_traceback(tb)
        assert 'File "cmk/gui/views.py", line 42, in render_view' in result
        # Empty text should not produce an extra line
        lines = result.strip().split("\n")
        assert len(lines) == 1

    def test_empty_traceback(self) -> None:
        assert format_traceback([]) == ""

    def test_mixed_frame_lengths(self) -> None:
        tb = [
            ["file1.py", "1", "func1", "code1"],
            ["file2.py", "2", "func2"],
        ]
        result = format_traceback(tb)
        assert "file1.py" in result
        assert "file2.py" in result


class TestLoadLocalCrash:
    @staticmethod
    def _make_crash_dir(
        tmp_path: Path,
        site: str = "mysite",
        crash_type: str = "gui",
        crash_id: str = "abc-123",
    ) -> Path:
        crash_dir = (
            tmp_path
            / "omd"
            / "sites"
            / site
            / "var"
            / "check_mk"
            / "crashes"
            / crash_type
            / crash_id
        )
        crash_dir.mkdir(parents=True)
        return crash_dir

    def test_load_full_gui_crash(self, tmp_path: Path) -> None:
        crash_dir = self._make_crash_dir(
            tmp_path, site="prod01", crash_type="gui", crash_id="abc12345-dead-beef"
        )
        crash_info = {
            "id": "abc12345-dead-beef",
            "crash_type": "gui",
            "version": "2.4.0p5",
            "time": 1700000000,
            "exc_type": "KeyError",
            "exc_value": "Missing key 'host_address' in row data",
            "exc_traceback": [
                ["cmk/gui/views/inventory.py", "312", "render_view", "row = _fetch_row(host_name)"],
                [
                    "cmk/gui/plugins/views/inventory.py",
                    "87",
                    "_fetch_row",
                    "address = row['host_address']",
                ],
            ],
            "local_vars": {
                "host_name": "db-server.prod.megacorp.de",
                "user": "admin@megacorp.de",
                "remote_addr": "172.20.5.44",
            },
            "os": "Ubuntu 22.04.3 LTS",
            "edition": "cee",
            "core": "cmc",
            "python_version": "3.12.3",
            "details": {"page": "view.py", "user": "admin@megacorp.de"},
        }
        (crash_dir / "crash.info").write_text(json.dumps(crash_info))

        result = _load_local_crash(crash_dir)

        assert result["crash_id"] == "abc12345-dead-beef"
        assert result["crash_type"] == "gui"
        assert result["cmk_version"] == "2.4.0p5"
        assert result["exc_type"] == "KeyError"
        assert result["exc_value"] == "Missing key 'host_address' in row data"
        assert result["os"] == "Ubuntu 22.04.3 LTS"
        assert result["edition"] == "cee"
        assert result["core"] == "cmc"
        assert result["python_version"] == "3.12.3"
        assert result["local_vars"]["host_name"] == "db-server.prod.megacorp.de"
        assert result["details"]["page"] == "view.py"
        assert "prod01" in result["source"]
        assert str(crash_dir) == result["local_path"]

    def test_load_check_crash_with_extra_files(self, tmp_path: Path) -> None:
        crash_dir = self._make_crash_dir(
            tmp_path, site="monitoring", crash_type="check", crash_id="def-456"
        )
        crash_info = {
            "id": "def-456",
            "crash_type": "check",
            "version": "2.3.0p22",
            "time": 1695000000,
            "exc_type": "MKAgentError",
            "exc_value": "Cannot connect to host webshop.retail.acme-corp.eu:6556",
        }
        (crash_dir / "crash.info").write_text(json.dumps(crash_info))
        (crash_dir / "agent_output").write_text(
            "<<<check_mk>>>\nVersion: 2.3.0p22\nAgentOS: linux\n"
            "<<<tcp>>>\n10.42.100.7:6556 REFUSED\n"
        )
        (crash_dir / "snmp_info").write_text(".1.3.6.1.2.1.1.1.0 = Linux monitoring 5.15.0\n")

        result = _load_local_crash(crash_dir)

        assert result["crash_id"] == "def-456"
        assert result["cmk_version"] == "2.3.0p22"
        assert "monitoring" in result["source"]
        assert "agent_output" in result
        assert "<<<check_mk>>>" in result["agent_output"]
        assert "10.42.100.7" in result["agent_output"]
        assert "snmp_info" in result
        assert ".1.3.6.1.2.1.1.1.0" in result["snmp_info"]

    def test_load_missing_crash_info_raises(self, tmp_path: Path) -> None:
        crash_dir = self._make_crash_dir(tmp_path)
        # No crash.info written — should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            _load_local_crash(crash_dir)

    def test_load_corrupt_crash_info_raises(self, tmp_path: Path) -> None:
        crash_dir = self._make_crash_dir(tmp_path)
        (crash_dir / "crash.info").write_text("not valid json {{{")
        with pytest.raises(json.JSONDecodeError):
            _load_local_crash(crash_dir)

    def test_site_name_unknown_when_no_sites_dir(self, tmp_path: Path) -> None:
        """If crash dir path doesn't contain 'sites', site_name should be 'unknown'."""
        crash_dir = tmp_path / "some" / "other" / "path" / "gui" / "crash-999"
        crash_dir.mkdir(parents=True)
        (crash_dir / "crash.info").write_text(json.dumps({"id": "crash-999", "time": 0}))

        result = _load_local_crash(crash_dir)
        assert "unknown" in result["source"]


class TestApiError:
    def test_is_exception(self) -> None:
        with pytest.raises(ApiError, match="test error"):
            raise ApiError("test error")
