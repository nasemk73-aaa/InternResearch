#!/usr/bin/env python3
# Copyright (C) 2026 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

import importlib.machinery
import importlib.util
import json
import sys

werks_config_file = sys.argv[1]

loader = importlib.machinery.SourceFileLoader("c", werks_config_file)
if (spec := importlib.util.spec_from_file_location("c", werks_config_file, loader=loader)) is None:
    raise ImportError(f"Could not load {werks_config_file}")

werks_config = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(werks_config)

result: dict[str, list[str] | dict[str, list[str]]] = {
    name: [item[0] for item in getattr(werks_config, name, [])]
    for name in ["editions", "components", "classes", "levels", "compatible"]
}

result["edition_components"] = {
    ed: [item[0] for item in comps]
    for ed, comps in getattr(werks_config, "edition_components", {}).items()
}

sys.stdout.write(json.dumps(result, indent=2) + "\n")
