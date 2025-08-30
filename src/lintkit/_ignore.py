# SPDX-FileCopyrightText: © 2025 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Implementation of `ignore` related functionalities.

Warning:
    This module is internal and used by implemented `rule`s
    to take `ignore` (`noqa`) lines into consideration.

Note:
    See `settings` module on how to set the ignore strings.

"""

from __future__ import annotations

import dataclasses
import re
import typing

if typing.TYPE_CHECKING:
    import pathlib

    from collections.abc import Iterator

    from .rule import Rule

from . import error, settings


@dataclasses.dataclass(kw_only=True)
class Span:
    """Class describing span of lines.

    Helper representing `start` and `end`
    of `noqa`s.

    Attributes:
        start:
            Beginning of the span
        end:
            End of the span

    """

    start: int
    end: int

    def __contains__(self, line: int) -> bool:
        """Whether a given line is within the `span`.

        Args:
            line:
                Line number to verify

        Returns:
            `True` if `line` is within the `span`, `False` otherwise.
        """
        return self.start <= line <= self.end


def file(rule: Rule, content: str) -> bool:
    """Check if a file contains an ignore string for a given rule.

    Args:
        rule:
            Rule to check against
        content:
            Content of the file to check

    Returns:
        `True` if the file contains an ignore whole file string
        for a given rule, `False` otherwise.

    """
    return (
        re.search(
            settings.ignore_file.format(name=settings.name, code=rule.code),
            content,
        )
        is not None
    )


def spans(file: pathlib.Path, rule: Rule, lines: list[str]) -> Iterator[Span]:
    # ~ O(r*l) time complexity :/
    """Get spans of lines that are ignored for a given rule.

    Warning:
        Raises `error` if the `span` is not closed properly.
        If it's `closed` but not opened, the span will be ignored.

    Args:
        file:
            Path to the file for which spans are calculated.
        rule:
            Rule to check against
        lines:
            Lines of the file to check

    Raises:
        error.IgnoreRangeError:
            If there is an unclosed ignore range (has `start`, but no `end).

    Yields:
        Spans of lines that are ignored for a given rule.

    """
    start_regex = re.compile(
        settings.ignore_span_start.format(name=settings.name, code=rule.code)
    )
    end_regex = re.compile(
        settings.ignore_span_end.format(name=settings.name, code=rule.code)
    )

    start = None
    for i, line in enumerate(lines):
        if start is None:
            if start_regex.search(line) is not None:
                start = i
        elif end_regex.search(line) is not None:
            yield Span(start=start, end=i)
            start = None

    if start is not None:
        raise error.IgnoreRangeError(file, start, line=lines[start])
