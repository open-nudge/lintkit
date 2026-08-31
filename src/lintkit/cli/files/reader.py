# SPDX-FileCopyrightText: © 2026 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Callable file argument readers."""

from __future__ import annotations

import abc
import pathlib
import typing

if typing.TYPE_CHECKING:
    from collections.abc import Iterable


class Base(abc.ABC):
    """Base callable that reads file arguments."""

    @abc.abstractmethod
    def __call__(
        self, paths: Iterable[str | pathlib.Path]
    ) -> Iterable[str | pathlib.Path]:
        """Read file arguments.

        Args:
            paths:
                File or directory arguments.

        Returns:
            File paths to check.

        """
        raise NotImplementedError


class Default(Base):
    """Reader that returns file arguments unchanged."""

    @typing.override
    def __call__(
        self, paths: Iterable[str | pathlib.Path]
    ) -> Iterable[str | pathlib.Path]:
        """Return file arguments unchanged and in input order.

        Args:
            paths:
                File arguments.

        Returns:
            The unchanged file arguments.

        """
        return paths


class Recursive(Base):
    """Reader that recursively expands directory arguments."""

    def __init__(self, suffix: str) -> None:
        """Configure recursive directory matching.

        Args:
            suffix:
                File suffix to match below directory arguments.

        """
        self.suffix: str = suffix

    @typing.override
    def __call__(
        self, paths: Iterable[str | pathlib.Path]
    ) -> Iterable[str | pathlib.Path]:
        """Yield resolved files from explicit and directory arguments.

        Args:
            paths:
                File or directory arguments.

        Yields:
            Resolved, first-seen file paths without canonical duplicates.

        """
        seen: set[pathlib.Path] = set()
        for value in paths:
            path = pathlib.Path(value).resolve()
            candidates = (
                path.rglob(f"*{self.suffix}") if path.is_dir() else (path,)
            )
            for candidate in candidates:
                resolved = candidate.resolve()
                if resolved not in seen:  # pragma: no branch
                    seen.add(resolved)
                    yield resolved
