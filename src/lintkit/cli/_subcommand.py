# SPDX-FileCopyrightText: © 2025 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""CLI subcommands."""

from __future__ import annotations

import sys
import typing

from .. import _run, registry, settings

if typing.TYPE_CHECKING:
    import argparse

    from collections.abc import Iterable


def check(
    args: argparse.Namespace,
    include_codes: Iterable[int] | None = None,
    exclude_codes: Iterable[int] | None = None,
    end_mode: typing.Literal["first", "all"] = "all",
) -> typing.NoReturn:
    """Calculate semantic versioning based on commit messages.

    Outputs version and (optionally) sha of a commit
    related to this version (the last one in commit chain).

    This output allows to later compare git trees and inferred
    versions if necessary.

    Args:
        args:
            Arguments from the CLI.
        include_codes:
            Codes to include (likely obtained from a config file or a-like)
        exclude_codes:
            Codes to exclude (likely obtained from a config file or a-like).
        end_mode:
            Whether to stop after the first error or run all rules
            (likely obtained from a config file or a-like).

    """
    sys.exit(
        int(
            _run.run(  # pyright: ignore[reportArgumentType]
                args.files,
                include_codes,
                exclude_codes,
                end_mode,
                output=False,
            )
        )
    )


def rules(
    include_codes: Iterable[int] | None = None,
    exclude_codes: Iterable[int] | None = None,
) -> typing.NoReturn:
    """Calculate semantic versioning based on commit messages.

    Outputs version and (optionally) sha of a commit
    related to this version (the last one in commit chain).

    This output allows to later compare git trees and inferred
    versions if necessary.

    Args:
        args:
            Arguments from the CLI.
        include_codes:
            Codes to include (likely obtained from a config file or a-like)
        exclude_codes:
            Codes to exclude (likely obtained from a config file or a-like).

    """
    enabled = registry._process(  # noqa: SLF001
        registry.codes(), include_codes, exclude_codes
    )
    header = ("Name", "Enabled", "Description")

    rows: list[tuple[str, str | bool, str]] = [header]
    for rule, code in zip(registry.rules(), registry.codes(), strict=False):
        rows.append(
            (
                f"{settings.name}{code}",
                code in enabled,
                rule.description(),
            )
        )

    maximum_widths = tuple(
        max(len(str(row[i])) for row in rows) for i in range(len(header))
    )

    print(_format_row(header, maximum_widths))  # noqa: T201
    print("-+-".join("-" * w for w in maximum_widths))  # noqa: T201

    # Skip header
    for row in rows[1:]:
        print(_format_row(row, maximum_widths))  # noqa: T201

    sys.exit(0)


def _format_row(
    row: tuple[str, bool | str, str], maximum_widths: tuple[int, ...]
) -> str:
    """Format row for display.

    Args:
        row:
            Row to format
            (contains rule name, whether it's enabled and description).
        maximum_widths:
            Maximum width of each name, enablement and description.

    Returns:
        Formatted row.

    """
    return " | ".join(
        str(col).ljust(maximum_widths[i]) for i, col in enumerate(row)
    )
