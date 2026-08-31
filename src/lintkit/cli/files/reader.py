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

    def __init__(
        self,
        suffix: str,
        ignore_directories: Iterable[str] | None = None,
    ) -> None:
        """Configure recursive directory matching.

        Args:
            suffix:
                File suffix to match below directory arguments.
            ignore_directories:
                Exact directory component names to exclude while expanding
                directory arguments.

        """
        self.suffix: str = suffix
        self.ignore_directories: frozenset[str] = (
            frozenset(ignore_directories)
            if ignore_directories is not None
            else frozenset()
        )

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
            directory = path.is_dir()
            candidates = path.rglob(f"*{self.suffix}") if directory else (path,)
            for candidate in candidates:
                resolved = candidate.resolve()
                if (
                    not (
                        directory
                        and self.ignore_directories.intersection(
                            resolved.parts[:-1]
                        )
                    )
                    and resolved not in seen
                ):  # pragma: no branch
                    seen.add(resolved)
                    yield resolved
