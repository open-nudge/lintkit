# SPDX-FileCopyrightText: © 2026 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Private MCP check tool composition."""

from __future__ import annotations

import typing

from .. import cli as command
from .. import output

if typing.TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from ..cli.files import reader


def check(
    files_default: Iterable[str | Path] | None,
    files_reader: reader.Base,
) -> typing.Callable[..., str]:
    """Select a check tool with the appropriate files schema.

    Args:
        files_default:
            Paths used when `files` is omitted. `None` selects a callable that
            requires `files`; any iterable selects one with captured defaults.
        files_reader:
            Reader applied to whichever paths the check selects.

    Returns:
        A check tool callable with the selected `files` schema.

    """
    if files_default is None:
        return _required(files_reader)
    return _with_defaults(tuple(files_default), files_reader)


def _required(
    files_reader: reader.Base,
) -> typing.Callable[..., str]:
    """Create a check tool that requires files.

    Args:
        files_reader:
            Reader applied to explicit paths.

    Returns:
        A check tool callable with required `files`.

    """

    def tool(files: list[str], names: list[str] | None = None) -> str:
        """Check explicit files and return plain diagnostics.

        Args:
            files:
                Paths to check.
            names:
                Full, case-sensitive rule names to check. `None` checks all
                rules.

        Returns:
            Plain diagnostics without a trailing newline.

        """
        return _run(files_reader(files), names)

    return tool


def _with_defaults(
    files_default: tuple[str | Path, ...],
    files_reader: reader.Base,
) -> typing.Callable[..., str]:
    """Create a check tool that falls back to captured paths.

    Args:
        files_default:
            Paths used when the returned callable receives no `files`.
        files_reader:
            Reader applied to explicit paths or captured defaults.

    Returns:
        A check tool callable with optional `files`.

    """

    def tool(
        files: list[str] | None = None,
        names: list[str] | None = None,
    ) -> str:
        """Check explicit files or the server's configured defaults.

        Args:
            files:
                Explicit paths to check. `None` uses the captured defaults.
            names:
                Full, case-sensitive rule names to check. `None` checks all
                rules.

        Returns:
            Plain diagnostics without a trailing newline.

        """
        selected = files_default if files is None else files
        return _run(files_reader(selected), names)

    return tool


def _run(files: Iterable[str | Path], names: list[str] | None) -> str:
    """Check paths and capture plain diagnostics.

    Args:
        files:
            Paths to check.
        names:
            Full, case-sensitive rule names to check. `None` checks all rules.

    Returns:
        Plain diagnostics without a trailing newline.

    """
    accumulator = output.Accumulator()
    with accumulator:
        _ = command.check(files, names, end_mode="all")
    return accumulator.finalize()
