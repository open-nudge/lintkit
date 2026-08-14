# SPDX-FileCopyrightText: © 2025, 2026 open-nudge <https://github.com/open-nudge>
# SPDX-FileContributor: szymonmaszke <github@maszke.co>
#
# SPDX-License-Identifier: Apache-2.0

"""Type definitions used in `lintkit`.

Note:
    This module is mostly used internally, unlikely to
    be directly useful for linter creators.

"""

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from collections.abc import Hashable


class GetItem(typing.Protocol):
    """Protocol used to type objects with `__getitem__` and `__contains__`."""

    def __getitem__(self, key: Hashable) -> typing.Any:
        """Signature of `__getitem__` method.

        Args:
            key:
                Key to get the value for (must implement `Hashable` interface).

        Returns:
            Value for the key.

        """

    def __contains__(self, key: Hashable) -> bool:
        """Signature of `__contains__` method.

        Args:
            key:
                Key to check for (must implement `Hashable` interface).

        Returns:
            True if the key is in the object, False otherwise.

        """
        # Dummy return value, necessary to due pyright checks
        return True
