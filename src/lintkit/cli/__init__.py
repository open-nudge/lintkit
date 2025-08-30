# SPDX-FileCopyrightText: © 2025 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""CLI entrypoint for `lintkit`.

This module allows you to create unified `CLI`s, so
you only need to define your rules.

Example:
    ```python
    import lintkit

    # Importing your custom rules
    import rules

    # Run the CLI over all files and all your rules.
    lintkit.cli.main(version="0.1.0")
    ```

"""

from __future__ import annotations

from ._main import main

__all__ = ["main"]
