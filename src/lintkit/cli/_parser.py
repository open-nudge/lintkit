# SPDX-FileCopyrightText: © 2025, 2026 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Parser of the lintkit CLI."""

from __future__ import annotations

import argparse
import pathlib
import textwrap
import typing

from .. import available, registry, settings

if typing.TYPE_CHECKING:
    from collections.abc import Iterable


def root(
    version: str,
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
    parser = _RootParser(**kwargs)

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
    _check(subparsers, files_help, pass_files)
    _rules(subparsers)
    _examples(subparsers)
    if available.MCP:
        _mcp(subparsers)

    return parser


def _check(
    subparsers: argparse._SubParsersAction[_RootParser],
    help_: str | None,
    pass_files: bool = True,  # noqa: FBT001, FBT002
) -> None:
    """Create `check` subcommand subparser.

    Args:
        subparsers:
            Object where this subparser will be registered.
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
            - File defaults and directory expansion depend on the linter's
            configuration.
        """),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    if help_ is None:  # pragma: no branch
        help_ = "Files to process (defaults and directories depend on linter configuration)"

    if pass_files:  # pragma: no branch
        _ = parser.add_argument(
            "files",
            nargs="*",
            type=pathlib.Path,
            default=(),
            help=help_,
        )

    _selectors(parser)

    _ = parser.add_argument(
        "--end_mode",
        choices=["all", "first"],
        default=None,
        help=textwrap.dedent("""\
        If 'first', end after the first error, if 'all' check everything.

        Default: the linter creator's configured mode.
        """),
    )
    _ = parser.add_argument(
        "--output",
        choices=("cli", "json"),
        default="cli",
        help="Output format (default: 'cli').",
    )


def _rules(subparsers: argparse._SubParsersAction[_RootParser]) -> None:
    """Create `rules` subcommand subparser.

    Args:
        subparsers:
            Object where this subparser will be registered.

    """
    parser = subparsers.add_parser(
        "rules",
        description="Display selected rules and their descriptions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    _selectors(parser)


def _examples(subparsers: argparse._SubParsersAction[_RootParser]) -> None:
    """Create `examples` subcommand subparser.

    Args:
        subparsers:
            Object where this subparser will be registered.

    """
    parser = subparsers.add_parser(
        "examples",
        description="Display usage examples for selected rules.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    _selectors(parser)


def _mcp(subparsers: argparse._SubParsersAction[_RootParser]) -> None:
    """Create the optional `mcp` subcommand parser.

    Args:
        subparsers:
            Object where this subparser will be registered.

    """
    parser = subparsers.add_parser(
        "mcp",
        description="Serve lintkit commands over MCP using stdio or HTTP.",
    )
    choices = ("check", "rules", "examples")
    _ = parser.add_argument(
        "--enable",
        nargs="*",
        choices=choices,
        default=None,
        help="Expose only these tools.",
    )
    _ = parser.add_argument(
        "--disable",
        nargs="*",
        choices=choices,
        default=None,
        help="Hide these tools after applying --enable.",
    )
    _ = parser.add_argument(
        "--name",
        default=settings._name(),  # noqa: SLF001
        help="Server name (default: linter name).",
    )
    _ = parser.add_argument(
        "--transport",
        choices=("stdio", "http"),
        default="stdio",
        help="Transport to use (default: stdio).",
    )
    _ = parser.add_argument("--host", help="HTTP bind host.")
    _ = parser.add_argument("--port", type=int, help="HTTP bind port.")
    _ = parser.add_argument("--path", help="HTTP endpoint path.")
    _ = parser.add_argument(
        "--stateful",
        action="store_true",
        help="Use legacy stateful HTTP operation.",
    )
    _ = parser.add_argument(
        "--host-origin-protection",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable or disable HTTP host and origin protection.",
    )
    _ = parser.add_argument(
        "--allowed-host",
        action="append",
        help="Allow an HTTP Host value; repeat to add values.",
    )
    _ = parser.add_argument(
        "--allowed-origin",
        action="append",
        help="Allow an HTTP Origin value; repeat to add values.",
    )


def _selectors(parser: argparse.ArgumentParser) -> None:
    """Add common full-name rule selectors.

    Args:
        parser:
            Subcommand parser to update.

    """
    names = tuple(f"{settings._name()}{code}" for code in registry.codes())  # noqa: SLF001
    _ = parser.add_argument(
        "--names",
        nargs="*",
        choices=names,
        default=None,
        metavar="NAME",
        help="Exact case-sensitive full rule names (default: all rules).",
    )


class _RootParser(argparse.ArgumentParser):
    """Root parser that validates cross-option MCP constraints."""

    @typing.override
    def parse_args(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        args: Iterable[str] | None = None,
        namespace: typing.Any = None,
    ) -> argparse.Namespace:
        """Parse arguments and reject HTTP options under stdio.

        Args:
            args:
                Arguments to parse, or process arguments when `None`.
            namespace:
                Namespace to populate, when supplied.

        Returns:
            Validated parsed arguments.

        """
        parsed: argparse.Namespace = super().parse_args(args, namespace)
        values = vars(parsed)
        if values.get("subcommand") != "mcp" or values["transport"] == "http":
            return parsed
        http_options = (
            values["host"],
            values["port"],
            values["path"],
            values["host_origin_protection"],
            values["allowed_host"],
            values["allowed_origin"],
        )
        if values["stateful"] or any(
            value is not None for value in http_options
        ):
            self.error("HTTP options require --transport http")
        return parsed
