# AGENTS.md

This file provides guidance to AI agents when working with code in this repository.

## Project Overview

parsedmarc is a Python module and CLI utility for parsing DMARC aggregate (RUA), forensic (RUF), and SMTP TLS reports. It reads reports from IMAP, Microsoft Graph, Gmail API, Maildir, mbox files, or direct file paths, and outputs to JSON/CSV, Elasticsearch, OpenSearch, Splunk, Kafka, S3, Azure Log Analytics, syslog, or webhooks.

## Common Commands

```bash
# Install with dev/build dependencies
pip install .[build]

# Run all tests with coverage
pytest --cov --cov-report=xml tests.py

# Run a single test
pytest tests.py::Test::testAggregateSamples

# Lint and format
ruff check .
ruff format .

# Test CLI with sample reports
parsedmarc --debug -c ci.ini samples/aggregate/*
parsedmarc --debug -c ci.ini samples/forensic/*

# Build docs
cd docs && make html

# Build distribution
hatch build
```

To skip DNS lookups during testing, set `GITHUB_ACTIONS=true`.

## Architecture

**Data flow:** Input sources → CLI (`cli.py:_main`) → Parse (`__init__.py`) → Enrich (DNS/GeoIP via `utils.py`) → Output integrations

### Key modules

- `parsedmarc/__init__.py` — Core parsing logic. Main functions: `parse_report_file()`, `parse_report_email()`, `parse_aggregate_report_xml()`, `parse_forensic_report()`, `parse_smtp_tls_report_json()`, `get_dmarc_reports_from_mailbox()`, `watch_inbox()`
- `parsedmarc/cli.py` — CLI entry point (`_main`), config file parsing (`_load_config` + `_parse_config`), output orchestration. Supports configuration via INI files, `PARSEDMARC_{SECTION}_{KEY}` environment variables, or both (env vars override file values).
- `parsedmarc/types.py` — TypedDict definitions for all report types (`AggregateReport`, `ForensicReport`, `SMTPTLSReport`, `ParsingResults`)
- `parsedmarc/utils.py` — IP/DNS/GeoIP enrichment, base64 decoding, compression handling
- `parsedmarc/mail/` — Polymorphic mail connections: `IMAPConnection`, `GmailConnection`, `MSGraphConnection`, `MaildirConnection`
- `parsedmarc/{elastic,opensearch,splunk,kafkaclient,loganalytics,syslog,s3,webhook,gelf}.py` — Output integrations

### Report type system

`ReportType = Literal["aggregate", "forensic", "smtp_tls"]`. Exception hierarchy: `ParserError` → `InvalidDMARCReport` → `InvalidAggregateReport`/`InvalidForensicReport`, and `InvalidSMTPTLSReport`.

### Configuration

Config priority: CLI args > env vars > config file > defaults. Env var naming: `PARSEDMARC_{SECTION}_{KEY}` (e.g. `PARSEDMARC_IMAP_PASSWORD`). Section names with underscores use longest-prefix matching (`PARSEDMARC_SPLUNK_HEC_TOKEN` → `[splunk_hec] token`). Some INI keys have short aliases for env var friendliness (e.g. `[maildir] create` for `maildir_create`). File path values are expanded via `os.path.expanduser`/`os.path.expandvars`. Config can be loaded purely from env vars with no file (`PARSEDMARC_CONFIG_FILE` sets the file path).

### Caching

IP address info cached for 4 hours, seen aggregate report IDs cached for 1 hour (via `ExpiringDict`).

## Code Style

- Ruff for formatting and linting (configured in `.vscode/settings.json`)
- TypedDict for structured data, type hints throughout
- Python ≥3.10 required
- Tests are in a single `tests.py` file using unittest; sample reports live in `samples/`
- File path config values must be wrapped with `_expand_path()` in `cli.py`
- Maildir UID checks are intentionally relaxed (warn, don't crash) for Docker compatibility
- Token file writes must create parent directories before opening for write
