load("@aspect_rules_py//py:defs.bzl", "py_library")

py_library(
    name = "scripts_py",
    srcs = ["get_werk_fields.py"],
)

sh_library(
    name = "scripts_sh",
    srcs = [
        "amend_werk_commit.sh",
        "gather_commits.sh",
    ],
)
