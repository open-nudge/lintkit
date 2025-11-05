# SPDX-FileCopyrightText: © 2025 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Official `lintkit` API documentation.

## General

`lintkit` is a Python library allowing you to quickly create
custom linters, while being flexible enough to be used in a complex
settings.

Warning:
    Start with [tutorials](/lintkit/tutorials) to get a feel of the framework.

## Core modules

When creating custom linter(s) you will be (likely) interested in these
core modules:

- [`lintkit.settings`][] - global settings
    (e.g. name, how `noqa`s should be named etc.)
- [`lintkit.rule`][] - core class for creating linting rules
- [`lintkit.loader`][] - file loaders mixins (e.g. `python` or `YAML`),
    tailoring rules to data
- [`lintkit.check`][] - what is `check`ed by a rule

and the following functionalities from [`lintkit`][]:

- [`Value`][lintkit.Value] - define rule output in a reusable manner
- [`run`][lintkit.run] - run all (or subset of) rules on a given set of
    files

Tip:
    Roam around the docs to get a better feel of what's available.

"""

from __future__ import annotations

from importlib.metadata import version

from . import (
    check,
    cli,
    error,
    loader,
    output,
    registry,
    rule,
    settings,
    type_definitions,
)
from ._run import run
from ._value import Pointer, Value

__version__ = version("lintkit")
"""Current lintkit version."""

del version

__all__: list[str] = [
    "Pointer",
    "Value",
    "__version__",
    "check",
    "cli",
    "error",
    "loader",
    "output",
    "registry",
    "rule",
    "run",
    "settings",
    "type_definitions",
]
