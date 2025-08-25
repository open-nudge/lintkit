<!--
SPDX-FileCopyrightText: © 2025 open-nudge <https://github.com/open-nudge>
SPDX-FileContributor: szymonmaszke <github@maszke.co>

SPDX-License-Identifier: Apache-2.0
-->

# Advanced linter

In this tutorial you will learn how to work
with [`lintkit`][]'s
[ast (abstract syntax tree)](https://docs.python.org/3/library/ast.html)
in Python.

> [!TIP]
> If you are unsure what `ast` is please read
> [`ast`](https://docs.python.org/3/library/ast.html) documentation
> or other guides/tutorials.

Afterwards you will be able to:

- create linters targeting subparts of the Python files
    (e.g. `class`, `def` or conditionals)
- how to share the `ast` across multiple rules
- how to use the provided [`lintkit.check`][] module
    to your advantage

> [!NOTE]
> You will largely focus on creating rules in this tutorial.
> If you wish to see an end-to-end example, check out
> [basic tutorial](basic.md) and
> [configuration](configure.md)

While the tutorial is titled "advanced" you should know
most of the building blocks by now.

> We will build a linter which verifies, that
> no `class` or `function` name contains
> words like `util(s)` or `helper(s)`.

## Defining checks

> [!CAUTION]
> In order to share the functionality we will heavily
> use (multiple) inheritance and
> [mixins](https://en.wikipedia.org/wiki/Mixin).

Let's start with `check`ers definitions:

```python
import lintkit


# abstract because we will have to define `regex` method
class _NoWord(lintkit.check.Regex):
    """Shared regex_flags function."""

    def regex_flags(self) -> int:
        """Lower or uppercase works."""
        return re.IGNORECASE


class _NoUtils(_NoWord):
    """Match utilities and its variations."""

    def regex(self) -> str:
        # Also _utils etc.
        return r"_?util(s|ities)?"


class _NoHelpers(_NoWord):
    """Match helpers and its variations."""

    def regex(self) -> str:
        return r"_?help(ers?)?"
```

This constitutes the __what__ while utilizing
[`lintkit.check.Regex`][] which, given a `str` applies
regex search
([`re.search`](https://docs.python.org/3/library/re.html#re.search))
to be precise)

## Obtaining values

Now it is time to define how we can obtain `ast` elements like `class`es
or `function`s.

> [!NOTE]
> Basic knowledge of [`ast`](https://docs.python.org/3/library/ast.html)
> module will come handy, as we will targets specific nodes types.

We will be using the following `ast` types:

- [`ast.ClassDef`](https://docs.python.org/3/library/ast.html#ast.ClassDef)
    for `class` definitions
- [`ast.FunctionDef`](https://docs.python.org/3/library/ast.html#ast.ClassDef)
    for `function` definitions

Fortunately, loading and processing of `Python` syntax is already performed
by the [`ast`](https://docs.python.org/3/library/ast.html) and
[`lintkit.loader.Python`][], see below:

```python
import abc
import ast

from collections.abc import Iterable

class _Definition(lintkit.rule.Node, lintkit.loader.Python, abc.ABC):
    @abc.abstractmethod
    def ast_class(self) -> type[ast.ClassDef | ast.FunctionDef]:
        # Type of class we are after in concrete definitions.
        # See _ClassDefinition and _FunctionDefinition below
        raise NotImplementedError

    def values(self) -> Iterable[lintkit.Value[str]]:
        # Yield node (class or function) names from a Python file
        data: dict[type[ast.AST], ast.AST] = self.getitem("nodes_map")
        for node in data[self.ast_class()]:
            yield lintkit.Value.from_python(node.name, node)


class _ClassDefinition(_Definition):
    def ast_class(self) -> type[ast.ClassDef]:
        return ast.ClassDef

class _FunctionDefinition(_Definition):
    def ast_class(self) -> type[ast.FunctionDef]:
        return ast.FunctionDef
```

Please note the following:

- [`lintkit.loader.Python`][] defines a few useful attributes
    (variations of `ast`) which allows linter creators creating
    Python rules easier. `nodes_map` is a `dict` mapping `ast` types
    to its instances (e.g. class definition to class definition instances).
- __[`self.getitem`][lintkit.loader.Loader.getitem] is a method you should
    use to get the data from any [`lintkit.loader.Loader`][] subclass__.
    This method works just like Python's `__getitem__`, but utilizes
    caching across multiple rules (files are loaded and parsed only once).
- [`lintkit.Value.from_python`][] allows us to keep any value
    while keeping the necessary metadata about the node.
- __We are `yield`ing multiple `Value`s__. These are all
    [`ast.ClassDef`s](https://docs.python.org/3/library/ast.html#ast.ClassDef)
    or
    [`ast.FunctionDef`s](https://docs.python.org/3/library/ast.html#ast.FunctionDef)

> [!NOTE]
> [`lintkit.loader.Python`][] __is not optimal memory or compute-wise__.
> If you find it a bottleneck, you might consider creating a custom
> `loader`

## Mixing it together

Once the above have been defined we can mix these elements to
create multiple rules:

```python
class ClassNoHelpers(_NoHelpers, _ClassDefinitions, code=1):
    """Verify `class` name contains no `helper` word (or its variations)."""

    def message(self, value: lintkit.Value[str]) -> str:
        return f"Class {value} contains helper(s) names."

class ClassNoUtils(_NoUtils, _ClassDefinitions, code=2):
    """Verify `class` name contains no `utils` word (or its variations)."""

    def message(self, value: lintkit.Value[str]) -> str:
        return f"Class {value} contains utils(s) names."

class FunctionNoHelpers(_NoHelpers, _FunctionDefinitions, code=3):
    """Verify `function` name contains no `helper` word (or its variations)."""

    def message(self, value: lintkit.Value[str]) -> str:
        return f"Function {value} contains helper(s) names."

class FunctionNoUtils(_NoUtils, _FunctionDefinitions, code=4):
    """Verify `function` name contains no `utils` word (or its variations)."""

    def message(self, value: lintkit.Value[str]) -> str:
        return f"Function {value} contains util(s) names."
```

> [!IMPORTANT]
> __Order of inheritance matters__. It should go as follows:
> [`lintkit.check.Check`][], [`lintkit.loader.Loader`][] and
> [`lintkit.rule.Rule`][] (or their respective subclasses)

> [!TIP]
> You could further refactor the above rules to reuse `message` method.
> Left as is to be more approachable.

After mixing we can run these rules on some Python files, an example runner
could be:

```python
import pathlib
import sys

import lintkit

# Assuming this is where the rules were defined
import rules

# Defining linter name here is also fine
lintkit.settings.name: str = "MY-ADVANCED-LINTER"

if __name__ == "__main__":
    sys.exit(lintkit.run(*list(pathlib.Path(".").rglob("*.py"))))
```

## Next steps

Check one of the following tutorials to learn more about
what you can do with `lintkit`:

- [Basic tutorial](basic.md) showcasing `lintkit` capabilities
- [Configuring linter](configure.md) via
    [`loadfig`](https://github.com/open-nudge/loadfig)
    (or other tool)
- [File rules](file.md) (__extension of this tutorial__)
