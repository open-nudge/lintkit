# SPDX-FileCopyrightText: © 2025 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Module defining available extras."""

from __future__ import annotations

import importlib.util


def _modules_exist(*names: str) -> bool:
    """Check if module(s) are installed.

    Used for conditional imports throughout the project and conditional
    definitions of various functionalities.

    Args:
        *names: Module names to check.

    Returns:
        True if all modules are installed, False otherwise.
    """
    return all(importlib.util.find_spec(name) is not None for name in names)


RICH: bool = _modules_exist("rich")
"""Whether [Rich](https://github.com/Textualize/rich) is available.

It is used for pretty printing and enhanced terminal output.
"""

YAML: bool = _modules_exist("ruamel")
"""Whether [ruamel.yaml](https://yaml.dev/doc/ruamel-yaml/) is available.

It is used to parse YAML files and create their rules.
"""

TOML: bool = _modules_exist("tomlkit")
"""Whether [tomlkit](https://tomlkit.readthedocs.io/en/latest/) is available.

It is used to parse TOML files and create their rules.
"""
