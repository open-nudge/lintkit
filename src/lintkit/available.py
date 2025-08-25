# SPDX-FileCopyrightText: © 2025 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Information about available extra libraries.

Note:
    You can install these packages by specifying `extras`, e.g.
    `pip install lintkit[rich, toml, yaml]`

One can use the values "as is":

Example:
    ```python
    import lintkit

    if lintkit.available.RICH:
        print("rich library installed!")
    ```

"""

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
"""`Bool` indicating [rich](https://github.com/Textualize/rich) availability.

Used automatically for pretty printing and colorful terminal output.
"""

YAML: bool = _modules_exist("ruamel")
"""`Bool` indicating [ruamel](https://yaml.dev/doc/ruamel-yaml/) availability.

Used to parse `YAML` and create rules for it.
"""

TOML: bool = _modules_exist("tomlkit")
"""`Bool` indicating [tomlkit](https://tomlkit.readthedocs.io) availability.

Used to parse `TOML` and create rules for it.
"""
