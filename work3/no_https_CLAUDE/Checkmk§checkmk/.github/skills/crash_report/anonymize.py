#!/usr/bin/env python3
# Copyright (C) 2026 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

"""Anonymize sensitive data in crash report JSON files.

This script finds and replaces sensitive information while preserving context:
- IP addresses -> 10.x.x.x, 192.168.x.x, etc.
- Email addresses -> user1@example.com, user2@example.com, etc.
- Hostnames/domains -> host1.example.com, host2.example.com, etc.

Consistent replacements: Same value always maps to same anonymized value.
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any


class Anonymizer:
    def __init__(self) -> None:
        self.ip_mapping: dict[str, str] = {}
        self.email_mapping: dict[str, str] = {}
        self.hostname_mapping: dict[str, str] = {}
        self.ip_counter = 1
        self.email_counter = 1
        self.hostname_counter = 1

    def anonymize_ip(self, ip: str) -> str:
        """Anonymize IP address with consistent mapping."""
        if ip in self.ip_mapping:
            return self.ip_mapping[ip]

        octets = ip.split(".")
        third = self.ip_counter // 256
        fourth = self.ip_counter % 256
        if third > 255:
            raise ValueError(f"IP anonymization counter overflow at {self.ip_counter}")

        # Preserve private vs public IP structure (RFC 1918)
        if octets[0] == "10" or (octets[0] == "192" and octets[1] == "168"):
            anon_ip = f"10.0.{third}.{fourth}"
        elif octets[0] == "172" and 16 <= int(octets[1]) <= 31:
            anon_ip = f"172.16.{third}.{fourth}"
        else:
            anon_ip = f"203.0.{third}.{fourth}"

        self.ip_mapping[ip] = anon_ip
        self.ip_counter += 1
        return anon_ip

    def anonymize_email(self, email: str) -> str:
        """Anonymize email address with consistent mapping."""
        if email in self.email_mapping:
            return self.email_mapping[email]

        anon_email = f"user{self.email_counter}@example.com"
        self.email_mapping[email] = anon_email
        self.email_counter += 1
        return anon_email

    def anonymize_hostname(self, hostname: str) -> str:
        """Anonymize hostname/domain with consistent mapping."""
        if hostname in self.hostname_mapping:
            return self.hostname_mapping[hostname]

        # Preserve structure: hostname.domain.com -> hostN.example.com
        if "." in hostname:
            anon_hostname = f"host{self.hostname_counter}.example.com"
        else:
            anon_hostname = f"host{self.hostname_counter}"

        self.hostname_mapping[hostname] = anon_hostname
        self.hostname_counter += 1
        return anon_hostname

    def anonymize_string(self, text: str) -> tuple[str, list[str]]:
        """Anonymize sensitive data in a string. Returns (anonymized_text, findings)."""

        findings: list[str] = []

        # Pattern for IP addresses (IPv4)
        ip_pattern = r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"

        def _replace_ip(m: re.Match[str]) -> str:
            ip = m.group(0)
            anon_ip = self.anonymize_ip(ip)
            if ip != anon_ip:
                findings.append(f"IP: {ip} -> {anon_ip}")
            return anon_ip

        text = re.sub(ip_pattern, _replace_ip, text)

        # Pattern for email addresses
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"

        def _replace_email(m: re.Match[str]) -> str:
            email = m.group(0)
            if email.endswith("@example.com"):
                return email
            anon_email = self.anonymize_email(email)
            findings.append(f"Email: {email} -> {anon_email}")
            return anon_email

        text = re.sub(email_pattern, _replace_email, text)

        # Pattern for hostnames/domains (more conservative to avoid false positives)
        # Matches FQDN patterns but avoids common words
        hostname_pattern = r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}\b"
        _skip_extensions = {".py", ".get", ".js", ".ts", ".json", ".xml", ".html", ".sh"}
        _real_tlds = {
            "com",
            "org",
            "net",
            "edu",
            "gov",
            "io",
            "de",
            "uk",
            "eu",
            "info",
            "biz",
            "co",
            "us",
            "ca",
            "au",
            "fr",
            "it",
            "nl",
            "be",
            "ch",
            "at",
            "local",
            "internal",
            "lan",
            "intranet",
            "corp",
            "home",
            "test",
        }

        def _replace_hostname(m: re.Match[str]) -> str:
            hostname = m.group(0)
            if any(hostname.endswith(ext) for ext in _skip_extensions):
                return hostname
            if (
                hostname.endswith("example.com")
                or hostname.startswith("localhost")
                or "checkmk.com" in hostname
                or hostname in ("www.w3.org", "github.com")
            ):
                return hostname
            parts = hostname.split(".")
            tld = parts[-1].lower()
            if tld not in _real_tlds and len(parts) < 3:
                return hostname
            if len(parts) >= 2:
                anon_hostname = self.anonymize_hostname(hostname)
                findings.append(f"Hostname: {hostname} -> {anon_hostname}")
                return anon_hostname
            return hostname

        text = re.sub(hostname_pattern, _replace_hostname, text, flags=re.IGNORECASE)

        return text, findings

    # Dict keys whose values should never be anonymized
    _safe_keys = {
        "crash_id",
        "crash_type",
        "cmk_version",
        "exc_type",
        "exc_traceback",
        "python_version",
        "edition",
        "core",
        "os",
        "upload_time",
        "time",
        "id",
        "group_id",
        "crash_report_group_id",
        "num_crashes",
        "is_solved",
        "solved_at",
        "solved_by",
        "solved_versions",
        "jira_issue",
        "url",
        "source",
        "local_path",
        "version",
    }

    def anonymize_value(self, value: Any) -> tuple[Any, list[str]]:
        """Recursively anonymize values in data structures."""
        findings = []

        if isinstance(value, str):
            return self.anonymize_string(value)
        elif isinstance(value, dict):
            anonymized = {}
            for k, v in value.items():
                if k in self._safe_keys:
                    anonymized[k] = v
                else:
                    anon_v, v_findings = self.anonymize_value(v)
                    anonymized[k] = anon_v
                    findings.extend(v_findings)
            return anonymized, findings
        elif isinstance(value, list):
            anonymized_list: list[Any] = []
            for item in value:
                anon_item, item_findings = self.anonymize_value(item)
                anonymized_list.append(anon_item)
                findings.extend(item_findings)
            return anonymized_list, findings
        else:
            return value, []


def anonymize_file(file_path: Path, dry_run: bool = False) -> tuple[bool, list[str]]:
    """Anonymize a single crash report JSON file."""
    try:
        with open(file_path) as f:
            data = json.load(f)
    except Exception as e:
        return False, [f"Error loading {file_path}: {e}"]

    anonymizer = Anonymizer()
    anonymized_data, findings = anonymizer.anonymize_value(data)

    if not findings:
        return True, ["No sensitive data found"]

    if dry_run:
        return True, findings

    # Backup original file (copy, not rename, so original survives write failures)
    backup_path = file_path.parent / (file_path.name + ".bak")
    shutil.copy2(file_path, backup_path)

    # Write anonymized version
    with open(file_path, "w") as f:
        json.dump(anonymized_data, f, indent=2)

    findings.append(f"Backup saved to {backup_path.name}")
    return True, findings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "files", nargs="*", help="Specific JSON files to anonymize (default: all crash reports)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be anonymized without making changes",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all crash report files in tests/unit-crash-generated/data/",
    )

    args = parser.parse_args()

    # Determine files to process
    if args.files:
        files = [Path(f) for f in args.files]
    elif args.all:
        data_dir = Path("tests/unit-crash-generated/data/crash_reports")
        if not data_dir.exists():
            print(f"Error: {data_dir} not found", file=sys.stderr)
            sys.exit(1)
        files = list(data_dir.rglob("*.json"))
    else:
        print("Error: Specify files or use --all to process all crash reports")
        parser.print_help()
        sys.exit(1)

    if not files:
        print("No JSON files found")
        sys.exit(0)

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Processing {len(files)} file(s)...\n")

    total_findings = 0
    for file_path in files:
        print(f"{'=' * 60}")
        print(f"File: {file_path}")
        print(f"{'-' * 60}")

        success, findings = anonymize_file(file_path, args.dry_run)

        if not success:
            print(f"FAILED: {findings[0]}")
            continue

        if findings == ["No sensitive data found"]:
            print("No sensitive data found")
        else:
            for finding in findings:
                print(f"  {finding}")
            total_findings += len([f for f in findings if not f.startswith("Backup")])

        print()

    print(f"{'=' * 60}")
    if args.dry_run:
        print(f"[DRY RUN] Would anonymize {total_findings} sensitive value(s)")
        print("Run without --dry-run to apply changes")
    else:
        print(f"Anonymized {total_findings} sensitive value(s)")
        print("Original files backed up with .bak extension")


if __name__ == "__main__":
    main()
