<!--
SPDX-FileCopyrightText: © 2025 open-nudge <https://github.com/open-nudge>
SPDX-FileContributor: szymonmaszke <github@maszke.co>

SPDX-License-Identifier: Apache-2.0
-->

# File rules

Up until now our rules worked on `Node`s - subelements
(like Python's class definition or a variable in `TOML` file) of the file.

[`lintkit`][] allows you to also define rules working on __filenames__, which
might come handy in some situations.

In this tutorial, we will:

- Extend [Advanced tutorial](advanced.md) to also
    verify our Python files do not contain `helper`/`utils`.
- Define a rule running on __all elements of a file__ to verify
    we are not using too many `if`s.
- Define a rule running on __all files__ to verify all Python `class`
    names are unique.

## Rule on filename

> [!CAUTION]
> Make sure you have followed the [Advanced tutorial](advanced.md)
> tutorial before proceeding with this one!

In order to work with
[`pathlib.Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)
objects representing files we can use [`lintkit.loader.File`][]

```python
import lintkit


class _PythonFile(lintkit.rule.Node, lintkit.loader.File):
    @classmethod
    def skip(cls, filename: pathlib.Path, _: str) -> bool:
        return filename.suffix != ".py"

    def values(self) -> Iterable[lintkit.Value[str]]:
        yield lintkit.Value(str(self.file))

class FileNoHelpers(_NoHelpers, _PythonFile, code=5):
    """Verify file name contains no `helper` word (or its variations)."""

    def message(self, value: lintkit.Value[str]) -> str:
        return f"File '{value}' contains helper(s) names."

class FileNoUtils(_NoUtils, _PythonFile, code=6):
    """Verify file name contains no `utils` word (or its variations)."""

    def message(self, value: lintkit.Value[str]) -> str:
        return f"File {value} contains utils(s) names."
```

Adding this rule to the ones in [advanced tutorial](advanced.md) will
effectively check there are no `util` or `helper` files in the project.

> [!TIP]
> If you don't override [`lintkit.loader.File.skip`][] method
> [`lintkit.loader.File`][] will target every file.

## Whole file rule

> [!CAUTION]
> This and following subsections are independent from any previous tutorials.

[`lintkit.rule.File`][] allows you to define a rule which __acts
on all elements__ (however defined) __within a given file__.

An example should make it clearer:

```python
import ast
import itertools

import lintkit

lintkit.settings.name: str = "FILELINTER"
# You might not inherit from `check.Check` as long as you fulfil the interface
class TooManyConditionals(lintkit.loader.Python, lintkit.rule.File, code=0):
    def values(self) -> Iterable[lintkit.Value[str] | None]:

        data: dict[type[ast.AST], ast.AST] = self.getitem("nodes_map")
        # Get If and ternary operator nodes
        conditionals = itertools.chain(
            (data[typ] for typ in (ast.If, ast.IfExp))
        )
        # Just return every conditional in the file
        # We will count them, actual values don't matter
        for conditional in conditionals:
            yield lintkit.Value()

    def check(self, value: lintkit.Value):
        # Error for every value
        return True

    def finalize(self, fails: int) -> bool:
        # If there are more than `2` conditionals return True
        return fails > 2

    def message(self) -> str:
        return "More than '2' conditionals in the file"
```

> [!IMPORTANT]
> Unlike [`lintkit.rule.Node`][] __this `rule` does not fail when
> `check` returns `True`__. Instead, __it counts all fails__
> and uses [`lintkit.rule.File.finalize`][] to decide what
> constitutes a failure (in our case, if `check` returns `True`
> more than `2` times).

> [!TIP]
> You could have noticed, that `message` method has no arguments.
> As we are acting on multiple elements there is no straightforward meaning
> behind such argument, hence it is not within [`lintkit.rule.File`][]
> interface. __Remember you can always save any necessary variables
> within `self` if you need it though!__

This `Python` file would not break this rule:

```python
a, b = 2, 3
if a > b:
    print("a > b")
if b > a:
    print("b > a")
```

while this one would (three conditionals present):

```python
a, b = 2, 3
if a > b:
    print("a > b")
if b > a:
    print("b > a")
if a == b:
    print("b == a")
```

Now, if we run our rule, we will see the following error message:

```python
/conditionals.py:-:- FILELINTER0: More than "2" conditionals in the file
```

## All files rule

You can think of [`lintkit.rule.All`][] as a further generalization
of [`lintkit.rule.File`][] - you can gather info from all files
of interest (in our code `*.py`) and perform decisions based on that.

The following `rule` would verify whether __all `class` names in all files__
are unique:

```python
import collections
import ast

import lintkit

lintkit.settings.name: str = "ALLLINTER"

class TooManyConditionals(lintkit.loader.Python, lintkit.rule.All, code=0):
    def __init__(self) -> None:
        # Remember to call base class __init__ to perform setup
        super().__init__()

        self.class_names = collections.defaultdict(int)
        self.offending_classes: list[str] = []

    def values(self) -> Iterable[lintkit.Value[str] | None]:
        for klass in self.getitem("nodes_map")[ast.ClassDef]:
            self.class_names[klass.name] += 1
            # No need to return anything, this rule only gathers data
            yield None

    def check(self, _: lintkit.Value[str]) -> bool:
        # check just to be compatible with the interface
        return False

    def finalize(self, _: int) -> bool:
        # We are essentially doing the check of all data here
        unique_classes = True
        for klass, count in self.class_names.items():
            if count > 1:
                self.offending_classes.append(klass)
                unique_classes = False

        return not unique_classes

    def message(self) -> str:
        return (
            f"The same class names in multiple files: {self.offending_classes}"
        )
```

Now, if we have two Python files `A.py` and `B.py`, both with classes
`X` and `Y`, we would get the following error:

```python
/-:-:- ALLLINTER0: The same class names in multiple files: ['A', 'B']
```

## Next steps

Check one of the following tutorials to learn more about
what you can do with `lintkit`:

- [Basic tutorial](./basic.md) showcasing `lintkit` capabilities
- Prerequisite [advanced linter tutorial](advanced.md)
- [Configuring linter](configure.md) via
    [`loadfig`](https://github.com/open-nudge/loadfig)
    (or other tool)
