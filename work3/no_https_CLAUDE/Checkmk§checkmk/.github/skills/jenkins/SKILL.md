---
name: jenkins
description: Interacts with the Jenkins CI to get build and test job results
---

# Diagnosing a CI failure

Always start here — stages, test failures, and sub-job URLs in one call:

```bash
jenkins_build_data.py <URL> --include=stages,tests --failed-only
```

Drill into a triggered sub-job (shown as `Job: <url>` in stage output):

```bash
jenkins_build_data.py <triggered-job-url> --include=console,tests
```

Full console (default shows last 100 lines):

```bash
jenkins_build_data.py <URL> --include=full-console
```

Poll a running build:

```bash
jenkins_build_data.py <URL> --include=stages,tests --poll --poll-interval=60
```

Do NOT use curl — the tool handles auth, stage correlation, and test parsing.

# Downloading artifacts

Always use `/tmp/jenkins-artifacts` as the download directory:

```bash
jenkins_build_data.py <url> --download "<artifact>" --download-dir /tmp/jenkins-artifacts
```

# Parsing of the downloaded json

Prefer `jq` over `python3` commands.

# In case the commands jenkins_build_data.py is missing

Ask the user to clone the zeug_cmk git repository and add it to their PATH.
See also: https://wiki.lan.checkmk.net/x/4zBSCQ
