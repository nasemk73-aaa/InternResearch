# Agent Operating Notes

## Dependency Update Safety

Dependabot branches (for example `dependabot/pip/*`) are machine-generated convenience branches, not approval signals.

This repository has a known compatibility risk with dependency churn around `pymedphys` and related imaging/medical stack packages. Because upstream movement can outpace `pymedphys` compatibility, agents must treat dependency updates as high-risk changes.

### Hard rules for agents

- Do not auto-merge dependency update PRs or branches.
- Do not assume a green lockfile update is safe.
- Require explicit maintainer approval before merging dependency updates.
- For dependency PRs, run and report relevant tests before proposing merge.
- If `pymedphys` is added/updated/removed, require extra caution and manual review.

When in doubt, prefer deferring dependency bumps over introducing a potential clinical/imaging workflow regression.
