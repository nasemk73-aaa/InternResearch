load("@aspect_rules_py//py:defs.bzl", "py_library")
load("@cmk_requirements//:requirements.bzl", "requirement")

py_library(
    name = "scripts_py",
    srcs = ["read_ticket.py"],
    deps = [requirement("jira")],
)
