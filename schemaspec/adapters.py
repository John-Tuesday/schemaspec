"""Type conversion / specification
"""

__all__ = [
    "BaseType",
    "BoolAdapter",
    "ListAdapter",
    "SubgroupTypeAdapter",
    "FloatAdapter",
    "IntAdapter",
    "PathAdapter",
    "TypeAdapter",
    "StringAdapter",
]

import dataclasses
import pathlib
from typing import Protocol, override

type BaseType = str | int | float | bool | list | dict
"""Primative types which can be implicitly converted to and from Python."""


class TypeAdapter[T](Protocol):
    """Convert values to and from schema and python."""

    @property
    def type_spec(self) -> str:
        """Text to briefly show what valid input values are."""
        ...

    def is_valid(self, value: T) -> bool:
        """True if `value` is valid."""
        return True

    def export(self, value: T) -> str | None:
        """Export `value` to valid string representation."""
        ...

    def convert(self, value: BaseType) -> T | None:
        """Convert primative to full type."""
        ...


class ListAdapter[T](TypeAdapter[list[T]]):
    """List type adapter schema. Every element must be of type `T`."""

    _element_adapter: TypeAdapter[T]
    """Element-wise adapter."""

    def __init__(self, element_adapter: TypeAdapter[T]):
        self._element_adapter = element_adapter

    @property
    @override
    def type_spec(self) -> str:
        return f"[{self._element_adapter.type_spec},]"

    @override
    def is_valid(self, value: list[T]) -> bool:
        return all(map(self._element_adapter.is_valid, value))

    @override
    def export(self, value: list[T]) -> str | None:
        result = []
        for item in value:
            v = self._element_adapter.export(item)
            if not isinstance(v, str):
                return None
            result.append(v)
        return f"[{", ".join(result)}]"

    @override
    def convert(self, value: BaseType) -> list[T] | None:
        if not isinstance(value, list):
            return None
        result = []
        for item in value:
            v = self._element_adapter.convert(item)
            if v is None:
                return None
            result.append(v)
        return result


class SubgroupTypeAdapter[T](TypeAdapter[T]):
    """A given value is only valid if it is equal to one of given choices.

    If no choices are specified, act just like `TypeAdapter`.
    """

    def __init__(self, default_type_spec: str, choices: tuple[T, ...] = tuple()):
        self.__choices = choices
        self.__init_type_spec(default_type_spec)

    @property
    def choices(self) -> tuple[T, ...]:
        """Defines the valid choices of a value; empty means no constraint."""
        return self.__choices

    def __init_type_spec(self, default_spec: str) -> None:
        self.__type_spec = default_spec
        if not self.choices:
            return
        s = []
        for choice in self.choices:
            result = self.export(choice)
            if result is None:
                raise ValueError("Choice is not a valid type")
            s.append(result)
        self.__type_spec = " | ".join(s)

    @property
    @override
    def type_spec(self) -> str:
        return self.__type_spec

    @override
    def is_valid(self, value: T) -> bool:
        return not self.choices or value in self.choices


@dataclasses.dataclass
class BoolAdapter(SubgroupTypeAdapter[bool]):
    """Bool type schema."""

    def __init__(self, choices: tuple[bool, ...] = ()):
        super().__init__(default_type_spec="true | false", choices=choices)

    @override
    def is_valid(self, value: bool) -> bool:
        return isinstance(value, bool) and super().is_valid(value)

    @override
    def export(self, value: bool) -> str | None:
        if not self.is_valid(value):
            return None
        return "true" if value else "false"

    @override
    def convert(self, value: BaseType) -> bool | None:
        """Convert primative to full type."""
        if not isinstance(value, bool) or not self.is_valid(value):
            return None
        return value


@dataclasses.dataclass
class IntAdapter(SubgroupTypeAdapter[int]):
    """Int type schema."""

    def __init__(self, choices: tuple[int, ...] = ()):
        super().__init__(default_type_spec="<integer>", choices=choices)

    @override
    def is_valid(self, value: int) -> bool:
        return isinstance(value, int) and super().is_valid(value)

    @override
    def export(self, value: int) -> str | None:
        if not self.is_valid(value):
            return None
        return f"{value}"

    @override
    def convert(self, value: BaseType) -> int | None:
        """Convert primative to full type."""
        if not isinstance(value, int) or not self.is_valid(value):
            return None
        return value


@dataclasses.dataclass
class FloatAdapter(SubgroupTypeAdapter[float]):
    """Float type schema."""

    def __init__(self, choices: tuple[float, ...] = ()):
        super().__init__(default_type_spec="<float>", choices=choices)

    @override
    def is_valid(self, value: float) -> bool:
        return isinstance(value, float) and super().is_valid(value)

    @override
    def export(self, value: float) -> str | None:
        if not self.is_valid(value):
            return None
        return f"{value}"

    @override
    def convert(self, value: BaseType) -> float | None:
        """Convert primative to full type."""
        if not isinstance(value, float) or not self.is_valid(value):
            return None
        return value


@dataclasses.dataclass
class StringAdapter(SubgroupTypeAdapter[str]):
    """String type schema."""

    def __init__(self, choices: tuple[str, ...] = ()):
        super().__init__(default_type_spec='"<string>"', choices=choices)

    @override
    def is_valid(self, value: str) -> bool:
        return isinstance(value, str) and super().is_valid(value)

    @override
    def export(self, value: str) -> str | None:
        if not self.is_valid(value):
            return None
        return f'"{value}"'

    @override
    def convert(self, value: BaseType) -> str | None:
        """Convert primative to full type."""
        if not isinstance(value, str) or not self.is_valid(value):
            return None
        return value


class PathAdapter(TypeAdapter[pathlib.Path]):
    """Path type schema."""

    @property
    @override
    def type_spec(self) -> str:
        return '"<path>"'

    @override
    def is_valid(self, value: pathlib.Path) -> bool:
        return isinstance(value, pathlib.Path) and super().is_valid(value)

    @override
    def export(self, value: pathlib.Path) -> str | None:
        if not isinstance(value, pathlib.Path) or not self.is_valid(value):
            return None
        return f'"{value}"'

    @override
    def convert(self, value: BaseType) -> pathlib.Path | None:
        """Convert primative to full type."""
        if not isinstance(value, str):
            return None
        path = pathlib.Path(value)
        return path if self.is_valid(path) else None
