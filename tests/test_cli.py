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


@pytest.mark.parametrize(
    "files_default",
    ((p for p in pathlib.Path().rglob("*.py")), None),
)
@pytest.mark.parametrize("files_help", ("Go over files", None))
@pytest.mark.parametrize("include_codes", ([1, 2, 3], None))
@pytest.mark.parametrize("exclude_codes", ([1, 2, 3], None))
@pytest.mark.parametrize("end_mode", ("all", "first"))
@pytest.mark.parametrize(
    "args",
    (
        ["check", "tests/test_cli.py", "--exclude_codes", "1", "2", "3"],
        ["check"],
        ["rules"],
    ),
)
def test_smoke(  # noqa: PLR0913
    files_default: Iterable[pathlib.Path | str],
    files_help: str | None,
    include_codes: Iterable[int] | None,
    exclude_codes: Iterable[int] | None,
    end_mode: typing.Literal["all", "first"],
    args: list[str] | None,
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
        args:
            CLI arguments passed, if any (used mainly during testing).
            If no arguments are provided explicitly, the arguments from
            [`sys.argv`](https://docs.python.org/3/library/sys.html#sys.argv)
            will be used.

    """
    try:
        lintkit.cli.main(
            version="0.0.1",
            files_default=files_default,
            files_help=files_help,
            include_codes=include_codes,
            exclude_codes=exclude_codes,
            end_mode=end_mode,
            args=args,
            description="Dummy linter",
        )
    except lintkit.error.IgnoreRangeError as e:
        # For test_error.py
        assert "test_error.py" in str(e.file)  # noqa: PT017  # pragma: no cover
    except SystemExit as e:
        assert e.code in (0, 1)  # noqa: PT017
