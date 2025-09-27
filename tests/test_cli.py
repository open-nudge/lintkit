# SPDX-FileCopyrightText: © 2025 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Smoke test CLI entrypoint."""

from __future__ import annotations

import pathlib
import typing

import pytest

import lintkit

if typing.TYPE_CHECKING:
    from collections.abc import Iterable


@pytest.mark.parametrize("files_help", ("Go over files", None))
@pytest.mark.parametrize("include_codes", ([1, 2, 3], None))
@pytest.mark.parametrize("exclude_codes", ([1, 2, 3], None))
@pytest.mark.parametrize("end_mode", ("all", "first"))
@pytest.mark.parametrize("pass_files", (True, False))
@pytest.mark.parametrize(
    "args",
    (
        ["check", "tests/test_cli.py", "--exclude_codes", "1", "2", "3"],
        ["check"],
        ["rules"],
    ),
)
def test_smoke(  # noqa: PLR0913
    files_help: str | None,
    include_codes: Iterable[int] | None,
    exclude_codes: Iterable[int] | None,
    end_mode: typing.Literal["all", "first"],
    pass_files: bool,  # noqa: FBT001
    args: list[str],
) -> None:
    """Smoke test calculate subcommand.

    Args:
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

    """
    try:
        # Escape hatch, not files can be passed on CLI if pass_files is False.
        args = args if pass_files else args[:1]

        lintkit.cli.main(
            version="0.0.1",
            # Used to only process tests files, not everything,
            # excluding things like __pypackages__ etc.
            files_default=(
                p for p in pathlib.Path().glob("./tests/**") if p.is_file()
            ),
            files_help=files_help,
            include_codes=include_codes,
            exclude_codes=exclude_codes,
            end_mode=end_mode,
            pass_files=pass_files,
            args=args,
            description="Dummy linter",
        )
    except lintkit.error.IgnoreRangeError as e:
        # For test_error.py
        assert "test_error.py" in str(e.file)  # noqa: PT017  # pragma: no cover
    except SystemExit as e:
        assert e.code in (0, 1)  # noqa: PT017
