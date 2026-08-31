# SPDX-FileCopyrightText: © 2026 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Optional linter configuration loading."""

from __future__ import annotations

import typing

import loadfig

from . import settings


# Config is already cached by loadfig internally.
def config() -> dict[typing.Any, typing.Any]:
    """Load the current linter's configuration.

    Returns:
        The lowercase linter tool table, or an empty dictionary when Loadfig
        finds no configuration.

    """
    return loadfig.config(settings._name().lower())  # noqa: SLF001
