#!/usr/bin/env python3
# Copyright (C) 2026 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

"""Shared pytest fixtures with realistic crash report data."""

import pytest


@pytest.fixture()
def gui_crash_report() -> dict[str, object]:
    """Realistic GUI crash report with sensitive data scattered across nested structures."""
    return {
        "crash_id": "abc12345-dead-beef-cafe-123456789abc",
        "crash_type": "gui",
        "cmk_version": "2.4.0p5",
        "edition": "cee",
        "core": "cmc",
        "os": "Ubuntu 22.04.3 LTS",
        "python_version": "3.12.3",
        "time": 1700000000.123,
        "exc_type": "KeyError",
        "exc_value": "Missing key 'host_address' in row data for host db-server.prod.megacorp.de",
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
            "request_uri": "/mysite/check_mk/view.py?view_name=inv_host&host=db-server.prod.megacorp.de",
            "remote_addr": "172.20.5.44",
        },
        "details": {
            "page": "view.py",
            "vars": {
                "view_name": "inv_host",
                "host": "db-server.prod.megacorp.de",
            },
            "user": "admin@megacorp.de",
            "user_agent": "Mozilla/5.0",
        },
    }


@pytest.fixture()
def check_crash_report() -> dict[str, object]:
    """Realistic check crash report with IPs in free-text fields and agent output."""
    return {
        "crash_id": "def67890-1234-5678-9abc-def012345678",
        "crash_type": "check",
        "cmk_version": "2.3.0p22",
        "edition": "cre",
        "core": "nagios",
        "os": "Debian GNU/Linux 12",
        "python_version": "3.11.8",
        "time": 1695000000.0,
        "exc_type": "MKAgentError",
        "exc_value": (
            "Cannot connect to host webshop.retail.acme-corp.eu:6556"
            " (10.42.100.7): Connection refused"
        ),
        "exc_traceback": [
            ["cmk/base/checkers/agent.py", "204", "_execute", "output = self._fetch(...)"],
            ["cmk/base/checkers/tcp.py", "89", "_fetch", "sock.connect((address, port))"],
        ],
        "host": "webshop.retail.acme-corp.eu",
        "check_type": "tcp",
        "item": None,
        "description": "Check_MK Agent on webshop.retail.acme-corp.eu",
        "agent_output": (
            "<<<check_mk>>>\n"
            "Version: 2.3.0p22\n"
            "AgentOS: linux\n"
            "<<<tcp>>>\n"
            "10.42.100.7:6556 REFUSED\n"
            "<<<local>>>\n"
            "0 Backup - last_run=1695000000|size=1234 Backup OK"
        ),
        "snmp_info": None,
    }


@pytest.fixture()
def deeply_nested_crash() -> dict[str, object]:
    """Crash report with 4+ levels of nesting and mixed sensitive/safe data."""
    return {
        "crash_id": "nested-0000-1111-2222-333344445555",
        "crash_type": "gui",
        "cmk_version": "2.4.0p1",
        "os": "SLES 15 SP5",
        "time": 1710000000.0,
        "exc_type": "RuntimeError",
        "exc_value": "Failed processing on node controller.infra.example-net.de",
        "exc_traceback": [
            ["cmk/gui/wato/pages.py", "55", "action", "result = process(hosts)"],
        ],
        "details": {
            "level1": {
                "level2": {
                    "level3": {
                        "admin_email": "ops-team@example-net.de",
                        "gateway_ip": "192.168.50.1",
                        "hosts": [
                            {
                                "name": "node1.cluster.example-net.de",
                                "ip": "10.99.1.10",
                                "contact": "alice@example-net.de",
                            },
                            {
                                "name": "node2.cluster.example-net.de",
                                "ip": "10.99.1.11",
                                "contact": "bob@example-net.de",
                            },
                        ],
                    },
                    "safe_count": 42,
                },
                "monitor_host": "mon.infra.example-net.de",
            },
            "tags": ["production", "cluster"],
        },
    }
