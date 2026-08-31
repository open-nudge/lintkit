# SPDX-FileCopyrightText: © 2025, 2026 open-nudge <https://github.com/open-nudge>
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

from . import files
from ._main import main
from ._subcommand import check, examples, rules

__all__ = ["check", "examples", "files", "main", "rules"]
