# SPDX-FileCopyrightText: © 2026 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Callable default file providers."""

from __future__ import annotations

import abc
import pathlib
import typing

from ... import error
from . import reader

if typing.TYPE_CHECKING:
    from collections.abc import Iterable


class Base(abc.ABC):
    """Base callable that provides default file paths."""

    @abc.abstractmethod
    def __call__(self) -> Iterable[str | pathlib.Path]:
        """Provide default file paths.

        Returns:
            Default file paths.

        """
        raise NotImplementedError


class Default(Base):
    """Default provider that requires callers to supply files."""

    @typing.override
    def __call__(self) -> Iterable[str | pathlib.Path]:
        """Report that no default files are configured.

        Raises:
            lintkit.error.FilesMissingError:
                Always, because this provider has no files.

        """
        raise error.FilesMissingError


class Recursive(Base):
    """Provide matching files below one directory."""

    def __init__(
        self,
        suffix: str,
        directory: str | pathlib.Path | None = None,
        ignore_directories: Iterable[str] | None = None,
    ) -> None:
        """Configure recursive default files.

        Args:
            suffix:
                File suffix to match.
            directory:
                Root directory. `None` selects the current directory when the
                provider is called.
            ignore_directories:
                Exact directory component names to exclude recursively.

        """
        self.suffix: str = suffix
        self.directory: str | pathlib.Path | None = directory
        self.ignore_directories: frozenset[str] = (
            frozenset(ignore_directories)
            if ignore_directories is not None
            else frozenset()
        )

    @typing.override
    def __call__(self) -> Iterable[str | pathlib.Path]:
        """Provide resolved matching files below the configured directory.

        Returns:
            Matching files in natural recursive traversal order.

        """
        directory = (
            pathlib.Path.cwd() if self.directory is None else self.directory
        )
        return reader.Recursive(self.suffix, self.ignore_directories)(
            (pathlib.Path(directory).resolve(),)
        )
