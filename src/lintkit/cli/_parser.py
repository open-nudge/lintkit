# SPDX-FileCopyrightText: © 2025 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Parser of the `comver` CLI."""

from __future__ import annotations

import argparse
import pathlib
import textwrap
import typing

if typing.TYPE_CHECKING:
    from collections.abc import Iterable


def root(
    version: str,
    files_default: Iterable[str | pathlib.Path],
    files_help: str | None = None,
    pass_files: bool = True,  # noqa: FBT001, FBT002
    **kwargs: typing.Any,
) -> argparse.ArgumentParser:
    """Create the root CLI parser.

    Info:
        This function defines command line interface.

    Args:
        version:
            Version of the linter, likely following semantic versioning.
        files_default:
            Default set of files to iterate over __IF__ these were not provided
            on the command line (or provided in `args`) which take precedence.
        files_help:
            CLI help message about files. It allows you to have a more accurate
            description of the defaults (e.g. only Python files, see example).
        pass_files:
            Whether to pass files as CLI arguments or not.
            If `False`, the `check` subcommand will not accept any files
            as CLI arguments and will always use `files_default`.
            Useful when you want to restrict users to only use
            the default files (e.g. when integrating with a VCS hook).
        **kwargs:
            Keyword arguments to pass to the `argparse.ArgumentParser`

    Returns:
        The argument parser configured with all CLI commands.

    """
    parser = argparse.ArgumentParser(**kwargs)

    _ = parser.add_argument(
        "--version",
        action="version",
        version=version,
        help="Show the version and exit.",
    )

    subparsers = parser.add_subparsers(
        dest="subcommand",
        required=True,
    )
    _check(subparsers, files_default, files_help, pass_files)
    _rules(subparsers)

    return parser


def _check(
    subparsers,  # noqa: ANN001  # pyright: ignore [reportUnknownParameterType, reportMissingParameterType]
    default: Iterable[str | pathlib.Path],
    help_: str | None,
    pass_files: bool = True,  # noqa: FBT001, FBT002
) -> None:
    """Create `check` subcommand subparser.

    Args:
        subparsers:
            Object where this subparser will be registered.
        default:
            Default set of files to iterate over __IF__ these were not provided
            on the command line (or provided in `args`) which take precedence.
        help_:
            CLI help message about files. It allows you to have a more accurate
            description of the defaults (e.g. only Python files, see example).
        pass_files:
            Whether to pass files as CLI arguments or not.
            If `False`, the `check` subcommand will not accept any files
            as CLI arguments and will always use `files_default`.
            Useful when you want to restrict users to only use
            the default files (e.g. when integrating with a VCS hook).

    """
    parser = subparsers.add_parser(
        "check",
        description=textwrap.dedent("""\
        Check files against the linter.

        NOTE:

            - You can provide a list of files to check (useful when
            used with, for example, pre-commit)
            - If no FILES arguments are provided, this program runs on
            all Python files found in the current working directory.
            - If one of the arguments is directory, program will
            process each file within it.
        """),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    if help_ is None:
        help_ = "Files to process (default: all files in current working directory, recursively)"

    if pass_files:
        _ = parser.add_argument(
            "files",
            nargs="*",
            type=pathlib.Path,
            default=default,
            help=help_,
        )

    _ = parser.add_argument(
        "--exclude_codes",
        nargs="*",
        type=int,
        default=None,
        help=textwrap.dedent("""\
        Rule numbers to exclude (default: do not exclude any rule).

        Example:

            > %(prog)s --exclude_codes 1 2 3

        NOTE:

            - Arguments should be specified as integers
            - Configuration values (e.g. from pyproject.toml) take precedence
            - Exclusions take precedence over inclusions
        """),
    )
    _ = parser.add_argument(
        "--include_codes",
        nargs="*",
        type=int,
        default=None,
        help=textwrap.dedent("""\
        Rule numbers to exclude (default: do not exclude any rule).

        Example:

            # Only 3 will be included!
            > %(prog)s --include_codes 2 3 --exclude_codes 3

        NOTE:

            - Arguments should be specified as integers
            - Configuration values (e.g. from pyproject.toml) take precedence
            - Exclusions take precedence over inclusions
        """),
    )

    _ = parser.add_argument(
        "--end_mode",
        choices=["all", "first"],
        default="all",
        help=textwrap.dedent("""\
        If 'first', end after the first error, if 'all' check everything.

        Default: 'all'
        """),
    )


def _rules(subparsers) -> None:  # noqa: ANN001  # pyright: ignore [reportUnknownParameterType, reportMissingParameterType]
    """Create `rules` subcommand subparser.

    Args:
        subparsers:
            Object where this subparser will be registered.

    """
    _ = subparsers.add_parser(
        "rules",
        description="Display available rules, their status and description.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
