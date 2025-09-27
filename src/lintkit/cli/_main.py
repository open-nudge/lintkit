# SPDX-FileCopyrightText: © 2025 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Entrypoint for `lintkit`'s reusable CLI."""

from __future__ import annotations

import typing

from .. import error
from . import _parser, _subcommand

if typing.TYPE_CHECKING:
    import pathlib

    from collections.abc import Iterable


def main(  # noqa: PLR0913
    *,
    version: str,
    files_default: Iterable[str | pathlib.Path],
    files_help: str | None = None,
    include_codes: Iterable[int] | None = None,
    exclude_codes: Iterable[int] | None = None,
    end_mode: typing.Literal["first", "all"] = "all",
    pass_files: bool = True,
    args: list[str] | None = None,
    **kwargs: typing.Any,
) -> None:
    """Command-line entry point for the linter.

    Parses arguments and dispatches execution to the subcommands
    based on user input.

    Example:
        ```python
        import lintkit

        # Importing rules
        import rules

        # Run the CLI
        lintkit.cli.main(
            version="0.1.0",
            # Only iterate over Python files
            files_default=pathlib.Path(".").rglob("*.py"),
            files_help=(
                "Files to process (default: all Python files recursively)",
            ),
        )
        ```

    Args:
        version:
            Version of the linter, likely following semantic versioning.
        files_default:
            Default set of files to iterate over __IF__ these were not provided
            on the command line (or provided in `args`) which take precedence.
        files_help:
            CLI help message about files. It allows you to have a more accurate
            description of the defaults (e.g. only Python files, see example).
        include_codes:
            Codes to include (likely obtained from a config file or a-like)
        exclude_codes:
            Codes to exclude (likely obtained from a config file or a-like).
        end_mode:
            Whether to stop after the first error or run all rules
            (likely obtained from a config file or a-like).
        pass_files:
            Whether to pass files as CLI arguments or not.
            If `False`, the `check` subcommand will not accept any files
            as CLI arguments and will always use `files_default`.
            Useful when you want to restrict users to only use
            the default files (e.g. when integrating with a VCS hook).
        args:
            CLI arguments passed, if any (used mainly during testing).
            If no arguments are provided explicitly, the arguments from
            [`sys.argv`](https://docs.python.org/3/library/sys.html#sys.argv)
            will be used.
        **kwargs:
            Keyword arguments to pass __to the root parser__
            (`argparse.ArgumentParser`).

    """
    parsed_args = _parser.root(
        version,
        files_default,
        files_help,
        pass_files,
        **kwargs,
    ).parse_args(args)

    if not pass_files:
        parsed_args.files = files_default

    if parsed_args.subcommand == "check":
        _subcommand.check(parsed_args, include_codes, exclude_codes, end_mode)
    if parsed_args.subcommand == "rules":
        _subcommand.rules(include_codes, exclude_codes)

    # Cannot be anything else, but left to make pyright feel at peace
    raise error.LintkitInternalError  # pragma: no cover
