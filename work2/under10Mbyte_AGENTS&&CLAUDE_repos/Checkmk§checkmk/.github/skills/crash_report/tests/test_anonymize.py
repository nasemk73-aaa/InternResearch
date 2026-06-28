#!/usr/bin/env python3
# Copyright (C) 2026 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

import json
from pathlib import Path
from typing import Any

from ..anonymize import anonymize_file, Anonymizer


class TestAnonymizeIP:
    def test_private_ip_10(self) -> None:
        a = Anonymizer()
        result = a.anonymize_ip("10.1.2.3")
        assert result.startswith("10.0.")

    def test_private_ip_192(self) -> None:
        a = Anonymizer()
        result = a.anonymize_ip("192.168.1.100")
        assert result.startswith("10.0.")

    def test_private_ip_172(self) -> None:
        a = Anonymizer()
        result = a.anonymize_ip("172.16.5.10")
        assert result.startswith("172.16.")

    def test_public_ip(self) -> None:
        a = Anonymizer()
        result = a.anonymize_ip("8.8.8.8")
        assert result.startswith("203.0.")

    def test_consistent_mapping(self) -> None:
        a = Anonymizer()
        first = a.anonymize_ip("10.1.2.3")
        second = a.anonymize_ip("10.1.2.3")
        assert first == second

    def test_different_ips_get_different_mappings(self) -> None:
        a = Anonymizer()
        first = a.anonymize_ip("10.1.2.3")
        second = a.anonymize_ip("10.1.2.4")
        assert first != second


class TestAnonymizeEmail:
    def test_basic_email(self) -> None:
        a = Anonymizer()
        result = a.anonymize_email("admin@company.de")
        assert result == "user1@example.com"

    def test_consistent_mapping(self) -> None:
        a = Anonymizer()
        first = a.anonymize_email("admin@company.de")
        second = a.anonymize_email("admin@company.de")
        assert first == second

    def test_different_emails_get_different_mappings(self) -> None:
        a = Anonymizer()
        first = a.anonymize_email("admin@company.de")
        second = a.anonymize_email("user@other.org")
        assert first != second

    def test_counter_increments(self) -> None:
        a = Anonymizer()
        a.anonymize_email("a@x.com")
        result = a.anonymize_email("b@y.com")
        assert result == "user2@example.com"


class TestAnonymizeHostname:
    def test_fqdn(self) -> None:
        a = Anonymizer()
        result = a.anonymize_hostname("server.company.de")
        assert result == "host1.example.com"

    def test_simple_hostname(self) -> None:
        a = Anonymizer()
        result = a.anonymize_hostname("myserver")
        assert result == "host1"

    def test_consistent_mapping(self) -> None:
        a = Anonymizer()
        first = a.anonymize_hostname("server.company.de")
        second = a.anonymize_hostname("server.company.de")
        assert first == second


class TestAnonymizeString:
    def test_ip_in_string(self) -> None:
        a = Anonymizer()
        text, findings = a.anonymize_string("Connected to 10.1.2.3 on port 80")
        assert "10.1.2.3" not in text
        assert "10.0." in text
        assert len(findings) == 1
        assert findings[0].startswith("IP:")

    def test_email_in_string(self) -> None:
        a = Anonymizer()
        text, findings = a.anonymize_string("Contact: admin@company.de")
        assert "admin@company.de" not in text
        assert "@example.com" in text

    def test_example_com_email_not_anonymized(self) -> None:
        a = Anonymizer()
        text, findings = a.anonymize_string("Contact: user1@example.com")
        assert text == "Contact: user1@example.com"
        assert len(findings) == 0

    def test_hostname_in_string(self) -> None:
        a = Anonymizer()
        text, findings = a.anonymize_string("Host: server.company.de is down")
        assert "server.company.de" not in text
        assert "example.com" in text

    def test_checkmk_com_preserved(self) -> None:
        a = Anonymizer()
        text, findings = a.anonymize_string("Visit crash.checkmk.com for details")
        assert "crash.checkmk.com" in text

    def test_python_file_extension_not_anonymized(self) -> None:
        a = Anonymizer()
        text, findings = a.anonymize_string('File "cmk/gui/views.py", line 42')
        assert "views.py" in text

    def test_python_dotted_ref_not_anonymized(self) -> None:
        """Python references like self.page should not be treated as hostnames."""
        a = Anonymizer()
        text, _ = a.anonymize_string("self.page_menu crashed")
        assert "self.page_menu" in text

    def test_underscore_in_parts_skipped(self) -> None:
        a = Anonymizer()
        text, _ = a.anonymize_string("cls.validate_input raised error")
        # "cls.validate_input" has underscore -> should not be anonymized
        # but validate_input contains underscore so hostname pattern won't match well
        assert "validate" in text

    def test_real_tld_hostname_anonymized(self) -> None:
        a = Anonymizer()
        text, findings = a.anonymize_string("db.internal is unreachable")
        assert "db.internal" not in text
        assert len(findings) >= 1

    def test_unknown_tld_two_parts_skipped(self) -> None:
        """Two-part dotted ref with unknown TLD should not be anonymized."""
        a = Anonymizer()
        text, findings = a.anonymize_string("value.items returned empty")
        assert "value.items" in text

    def test_three_part_unknown_tld_anonymized(self) -> None:
        """Three-part hostname with unknown TLD should still be anonymized."""
        a = Anonymizer()
        text, findings = a.anonymize_string("host.sub.custom is down")
        assert "host.sub.custom" not in text

    def test_no_sensitive_data(self) -> None:
        a = Anonymizer()
        text, findings = a.anonymize_string("Just a plain string with no sensitive data")
        assert text == "Just a plain string with no sensitive data"
        assert len(findings) == 0

    def test_multiple_sensitive_values(self) -> None:
        a = Anonymizer()
        text, findings = a.anonymize_string(
            "Server 10.1.2.3 contacted admin@corp.de at host.corp.de"
        )
        assert "10.1.2.3" not in text
        assert "admin@corp.de" not in text
        assert "host.corp.de" not in text
        assert len(findings) == 3


class TestAnonymizeValue:
    def test_string_value(self) -> None:
        a = Anonymizer()
        result, findings = a.anonymize_value("Server at 10.1.2.3")
        assert "10.1.2.3" not in result

    def test_int_value(self) -> None:
        a = Anonymizer()
        result, findings = a.anonymize_value(42)
        assert result == 42
        assert len(findings) == 0

    def test_none_value(self) -> None:
        a = Anonymizer()
        result, findings = a.anonymize_value(None)
        assert result is None

    def test_list_value(self) -> None:
        a = Anonymizer()
        result, findings = a.anonymize_value(["10.1.2.3", "plain"])
        assert result[0] != "10.1.2.3"
        assert result[1] == "plain"

    def test_dict_value(self) -> None:
        a = Anonymizer()
        result, findings = a.anonymize_value({"contact_mail": "admin@corp.de", "count": 5})
        assert result["contact_mail"] != "admin@corp.de"
        assert result["count"] == 5

    def test_nested_dict(self) -> None:
        a = Anonymizer()
        result, findings = a.anonymize_value({"details": {"host": "server.corp.de", "port": 8080}})
        assert "server.corp.de" not in str(result)
        assert result["details"]["port"] == 8080

    def test_safe_keys_not_anonymized(self) -> None:
        a = Anonymizer()
        data = {
            "crash_id": "abc-123-def",
            "crash_type": "gui",
            "cmk_version": "2.4.0p5",
            "exc_type": "ValueError",
            "exc_traceback": [["cmk/gui/views.py", "42", "render", "self.page"]],
            "url": "https://crash.checkmk.com/gui/show/123",
            "contact_mail": "admin@corp.de",
        }
        result, findings = a.anonymize_value(data)

        # Safe keys preserved exactly
        assert result["crash_id"] == "abc-123-def"
        assert result["crash_type"] == "gui"
        assert result["cmk_version"] == "2.4.0p5"
        assert result["exc_type"] == "ValueError"
        assert result["exc_traceback"] == [["cmk/gui/views.py", "42", "render", "self.page"]]
        assert result["url"] == "https://crash.checkmk.com/gui/show/123"

        # Non-safe key anonymized
        assert result["contact_mail"] != "admin@corp.de"
        assert "@example.com" in result["contact_mail"]

    def test_all_safe_keys_preserved(self) -> None:
        """Every key in _safe_keys should pass through without anonymization."""
        a = Anonymizer()
        # Use a value that would normally be anonymized
        sensitive = "admin@corp.de"
        data = {key: sensitive for key in Anonymizer._safe_keys}  # noqa: SLF001
        result, findings = a.anonymize_value(data)

        for key in Anonymizer._safe_keys:  # noqa: SLF001
            assert result[key] == sensitive, f"Safe key {key!r} was unexpectedly anonymized"
        assert len(findings) == 0


class TestAnonymizeFile:
    def test_dry_run(self, tmp_path: Path) -> None:
        data = {"contact": "admin@corp.de", "ip": "10.1.2.3"}
        f = tmp_path / "crash.json"
        f.write_text(json.dumps(data))

        success, findings = anonymize_file(f, dry_run=True)
        assert success
        assert len(findings) >= 2

        # File should not be modified in dry-run
        assert json.loads(f.read_text()) == data

    def test_actual_anonymize(self, tmp_path: Path) -> None:
        data = {"contact": "admin@corp.de", "ip": "10.1.2.3"}
        f = tmp_path / "crash.json"
        f.write_text(json.dumps(data))

        success, findings = anonymize_file(f, dry_run=False)
        assert success

        # File should be modified
        result = json.loads(f.read_text())
        assert "admin@corp.de" not in str(result)
        assert "10.1.2.3" not in str(result)

        # Backup should exist
        assert (tmp_path / "crash.json.bak").is_file()

    def test_no_sensitive_data(self, tmp_path: Path) -> None:
        data = {"crash_type": "gui", "count": 5}
        f = tmp_path / "crash.json"
        f.write_text(json.dumps(data))

        success, findings = anonymize_file(f, dry_run=False)
        assert success
        assert findings == ["No sensitive data found"]

    def test_invalid_json(self, tmp_path: Path) -> None:
        f = tmp_path / "crash.json"
        f.write_text("not json")

        success, findings = anonymize_file(f, dry_run=False)
        assert not success
        assert "Error" in findings[0]


class TestAnonymizeFullReport:
    """Integration tests using realistic crash report fixtures."""

    def test_gui_crash_safe_keys_preserved(self, gui_crash_report: dict[str, Any]) -> None:
        a = Anonymizer()
        result, _ = a.anonymize_value(gui_crash_report)

        assert result["crash_id"] == "abc12345-dead-beef-cafe-123456789abc"
        assert result["crash_type"] == "gui"
        assert result["cmk_version"] == "2.4.0p5"
        assert result["exc_type"] == "KeyError"
        assert result["os"] == "Ubuntu 22.04.3 LTS"
        assert result["python_version"] == "3.12.3"
        assert result["time"] == 1700000000.123
        assert result["edition"] == "cee"
        assert result["core"] == "cmc"
        # exc_traceback is a safe key — preserved exactly including file paths
        assert result["exc_traceback"] == gui_crash_report["exc_traceback"]

    def test_gui_crash_sensitive_data_removed(self, gui_crash_report: dict[str, Any]) -> None:
        a = Anonymizer()
        result, findings = a.anonymize_value(gui_crash_report)
        result_str = json.dumps(result)

        assert "megacorp.de" not in result_str
        assert "admin@megacorp.de" not in result_str
        assert "db-server.prod.megacorp.de" not in result_str
        assert "172.20.5.44" not in result_str
        assert len(findings) >= 4  # at least: hostname, email, IP, and repeats

    def test_gui_crash_consistent_mapping(self, gui_crash_report: dict[str, Any]) -> None:
        """Same hostname in multiple fields maps to the same anonymized value."""
        a = Anonymizer()
        result, _ = a.anonymize_value(gui_crash_report)

        # db-server.prod.megacorp.de appears in local_vars.host_name and details.vars.host
        anon_hostname = result["local_vars"]["host_name"]
        assert result["details"]["vars"]["host"] == anon_hostname
        assert "example.com" in anon_hostname

    def test_check_crash_agent_output_anonymized(self, check_crash_report: dict[str, Any]) -> None:
        a = Anonymizer()
        result, _ = a.anonymize_value(check_crash_report)

        # agent_output is not a safe key — IPs inside should be anonymized
        assert "10.42.100.7" not in result["agent_output"]
        # But the agent section headers should survive
        assert "<<<check_mk>>>" in result["agent_output"]
        assert "<<<tcp>>>" in result["agent_output"]

    def test_check_crash_exc_value_anonymized(self, check_crash_report: dict[str, Any]) -> None:
        a = Anonymizer()
        result, _ = a.anonymize_value(check_crash_report)

        # exc_value is NOT a safe key — hostname and IP should be anonymized
        assert "10.42.100.7" not in result["exc_value"]
        assert "acme-corp.eu" not in result["exc_value"]

    def test_deeply_nested_all_anonymized(self, deeply_nested_crash: dict[str, Any]) -> None:
        a = Anonymizer()
        result, findings = a.anonymize_value(deeply_nested_crash)
        result_str = json.dumps(result)

        # All sensitive data at every nesting level should be gone
        assert "example-net.de" not in result_str
        assert "ops-team@example-net.de" not in result_str
        assert "alice@example-net.de" not in result_str
        assert "bob@example-net.de" not in result_str
        assert "192.168.50.1" not in result_str
        assert "10.99.1.10" not in result_str
        assert "10.99.1.11" not in result_str

        # Safe metadata preserved
        assert result["crash_id"] == "nested-0000-1111-2222-333344445555"
        assert result["cmk_version"] == "2.4.0p1"
        assert result["details"]["level1"]["level2"]["safe_count"] == 42
        assert result["details"]["tags"] == ["production", "cluster"]

    def test_172_range_boundary(self) -> None:
        """RFC 1918: only 172.16.0.0 - 172.31.255.255 are private."""
        a = Anonymizer()

        # 172.15.x.x is public
        assert a.anonymize_ip("172.15.0.1").startswith("203.0.")
        # 172.16.x.x is private (lower bound)
        assert a.anonymize_ip("172.16.0.1").startswith("172.16.")
        # 172.31.x.x is private (upper bound)
        assert a.anonymize_ip("172.31.255.1").startswith("172.16.")
        # 172.32.x.x is public
        assert a.anonymize_ip("172.32.0.1").startswith("203.0.")

    def test_anonymize_file_roundtrip(
        self, tmp_path: Path, gui_crash_report: dict[str, Any]
    ) -> None:
        """Write realistic crash report to disk, anonymize, reload, verify."""
        f = tmp_path / "crash.json"
        f.write_text(json.dumps(gui_crash_report, indent=2))

        success, findings = anonymize_file(f, dry_run=False)
        assert success
        assert any("megacorp" in f for f in findings)

        # Reload and verify valid JSON with no sensitive data
        result = json.loads(f.read_text())
        result_str = json.dumps(result)
        assert "megacorp.de" not in result_str
        assert "172.20.5.44" not in result_str
        assert "admin@megacorp.de" not in result_str

        # Safe keys still intact
        assert result["crash_id"] == "abc12345-dead-beef-cafe-123456789abc"
        assert result["crash_type"] == "gui"
