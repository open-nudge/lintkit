# SPDX-FileCopyrightText: © 2025, 2026 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Smoke test CLI entrypoint."""

from __future__ import annotations

import json
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
def test_smoke(  # noqa: PLR0913, PLR0917
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


@pytest.mark.parametrize(
    ("content", "expected_code", "expected_records"),
    (("value = 1\n", 0, 0), ("def test_run_example():\n    pass\n", 1, 1)),
)
def test_json_output(
    content: str,
    expected_code: int,
    expected_records: int,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test JSON output for clean and failing CLI runs.

    Args:
        content:
            Content of the checked file.
        expected_code:
            Expected CLI exit code.
        expected_records:
            Expected number of JSON records.
        tmp_path:
            Temporary directory used to create the checked file.
        capsys:
            Pytest fixture used to capture CLI output.

    """
    file = tmp_path / "example.py"
    _ = file.write_text(content)
    with pytest.raises(SystemExit) as exception:
        lintkit.cli.main(
            version="0.0.1",
            files_default=(),
            include_codes=(0,),
            args=["check", "--output", "json", str(file)],
        )
    records = json.loads(capsys.readouterr().out)
    assert (exception.value.code, len(records)) == (
        expected_code,
        expected_records,
    )


@pytest.mark.parametrize(
    ("names", "expected"),
    (
        (
            [],
            (
                "TEST0:\n\ndef test_run_example():\n    pass\n\ntest_run = True\n\n"
                "TEST1:\n\ndef miss_example():\n    pass\n"
            ),
        ),
        (
            ["TEST1", "TEST0"],
            (
                "TEST1:\n\ndef miss_example():\n    pass\n\n"
                "TEST0:\n\ndef test_run_example():\n    pass\n\ntest_run = True\n"
            ),
        ),
        (
            ["TEST0", "TEST0"],
            (
                "TEST0:\n\ndef test_run_example():\n    pass\n\ntest_run = True\n\n"
                "TEST0:\n\ndef test_run_example():\n    pass\n\ntest_run = True\n"
            ),
        ),
        (["TEST101", "TEST1"], "TEST1:\n\ndef miss_example():\n    pass\n"),
        (["TEST101"], ""),
    ),
)
def test_examples(
    names: list[str],
    expected: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test displayed examples, selector order, duplicates, and empty rules.

    Args:
        names:
            Full rule names to select.
        expected:
            Expected standard output.
        capsys:
            Pytest fixture used to capture CLI output.

    """
    with pytest.raises(SystemExit) as exception:
        lintkit.cli.main(
            version="0.0.1",
            files_default=(),
            args=["examples", *names],
        )
    assert (exception.value.code, capsys.readouterr().out) == (0, expected)
