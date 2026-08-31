# SPDX-FileCopyrightText: © 2025, 2026 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Entrypoint for `lintkit`'s reusable CLI."""

from __future__ import annotations

import typing

from .. import error, output, settings
from . import _parser, _subcommand
from .files import default, reader

if typing.TYPE_CHECKING:
    import pathlib

    from collections.abc import Iterable


def main(  # noqa: C901, PLR0912, PLR0913, PLR0915
    *,
    version: str,
    files_default: default.Base | None = None,
    files_reader: reader.Base | None = None,
    files_help: str | None = None,
    names: Iterable[str] | None = None,
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
            files_default=lintkit.cli.files.default.Recursive(".py"),
            files_reader=lintkit.cli.files.reader.Recursive(".py"),
            files_help=(
                "Files to process (default: all Python files recursively)",
            ),
        )
        ```

    Args:
        version:
            Version of the linter, likely following semantic versioning.
        files_default:
            Callable that provides files when explicit paths are not used.
        files_reader:
            Callable that reads the selected explicit or default paths.
        files_help:
            CLI help message about files. It allows you to have a more accurate
            description of the defaults (e.g. only Python files, see example).
        names:
            Full, case-sensitive rule names selected by default. `None`
            selects all rules.
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

    Raises:
        SystemExit:
            After a command finishes or argument parsing fails.
        lintkit.error.LintkitInternalError:
            If argument parsing returns an unknown subcommand.

    """
    if files_default is None:  # pragma: no branch
        files_default = default.Default()
    if files_reader is None:  # pragma: no branch
        files_reader = reader.Default()

    parser = _parser.root(
        version,
        files_help,
        pass_files,
        **kwargs,
    )
    parsed_args = parser.parse_args(args)

    if parsed_args.subcommand == "mcp":
        _mcp(parsed_args, files_default, files_reader)
        return

    selected_names = names if parsed_args.names is None else parsed_args.names
    if parsed_args.subcommand == "check":
        selected_end = (
            end_mode if parsed_args.end_mode is None else parsed_args.end_mode
        )
        try:
            selected_files = (
                parsed_args.files
                if pass_files and parsed_args.files
                else files_default()
            )
            _check(
                files_reader(selected_files),
                selected_names,
                selected_end,
                parsed_args.output,
            )
        except error.FilesMissingError as exception:  # pragma: no cover
            parser.error(str(exception))

    if parsed_args.subcommand == "rules":
        print(_subcommand.rules(selected_names))  # noqa: T201
        raise SystemExit(0)

    if parsed_args.subcommand == "examples":
        rendered = _subcommand.examples(selected_names)
        if rendered:  # pragma: no branch
            print(rendered)  # noqa: T201

        raise SystemExit(0)

    # Cannot be anything else, but left to make pyright feel at peace
    raise error.LintkitInternalError  # pragma: no cover


def _check(
    files: Iterable[str | pathlib.Path],
    names: Iterable[str] | None,
    end_mode: typing.Literal["first", "all"],
    output_name: typing.Literal["cli", "json"],
) -> typing.NoReturn:
    """Run the CLI-only check output and exit handling.

    Args:
        files:
            Files to check.
        names:
            Full rule names to check, or all rules when `None`.
        end_mode:
            Whether to stop after the first failure or run all rules.
        output_name:
            CLI output format.

    Raises:
        SystemExit:
            With status one when a selected rule fails, otherwise zero.

    """
    selected_output = (
        output.JSON() if output_name == "json" else settings._output()  # noqa: SLF001
    )
    with selected_output:
        failed = _subcommand.check(files, names, end_mode)
    raise SystemExit(int(failed))


def _mcp(
    parsed_args: typing.Any,
    files_default: default.Base,
    files_reader: reader.Base,
) -> None:
    """Start the selected MCP transport.

    Args:
        parsed_args:
            Parsed MCP command arguments.
        files_default:
            Default files configured by the linter.
        files_reader:
            Reader configured by the linter.

    """
    from .. import mcp  # noqa: PLC0415

    run_kwargs: dict[str, typing.Any] = {
        "transport": parsed_args.transport,
        "show_banner": False,
    }
    if parsed_args.transport == "http":
        _http_kwargs(run_kwargs, parsed_args)
    try:
        mcp_defaults = tuple(files_default())
    except error.FilesMissingError:
        mcp_defaults = None
    mcp.server(
        parsed_args.enable,
        parsed_args.disable,
        files_default=mcp_defaults,
        files_reader=files_reader,
        name=parsed_args.name,
    ).run(**run_kwargs)


def _http_kwargs(
    run_kwargs: dict[str, typing.Any], parsed_args: typing.Any
) -> None:
    """Add only explicit HTTP settings to FastMCP run options.

    Args:
        run_kwargs:
            Run options to update.
        parsed_args:
            Parsed MCP command arguments.

    """
    mappings = {
        "host": parsed_args.host,
        "port": parsed_args.port,
        "path": parsed_args.path,
        "host_origin_protection": parsed_args.host_origin_protection,
        "allowed_hosts": parsed_args.allowed_host,
        "allowed_origins": parsed_args.allowed_origin,
    }
    run_kwargs.update(
        (key, value) for key, value in mappings.items() if value is not None
    )
    if parsed_args.stateful:  # pragma: no branch
        run_kwargs["stateless"] = False
