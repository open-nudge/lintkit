# SPDX-FileCopyrightText: © 2025 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Official `lintkit` API documentation.

About:
    `lintkit` is a Python library allowing you to quickly create
    custom linters, while being flexible enough to be used in a complex
    settings.

"""

from __future__ import annotations

from importlib.metadata import version

from . import (
    check,
    error,
    loader,
    output,
    registry,
    rule,
    settings,
    type_definitions,
)
from ._run import run
from ._value import Value

__version__ = version("lintkit")
"""Current lintkit version."""

del version

__all__: list[str] = [
    "Value",
    "__version__",
    "check",
    "error",
    "loader",
    "output",
    "registry",
    "rule",
    "run",
    "settings",
    "type_definitions",
]
