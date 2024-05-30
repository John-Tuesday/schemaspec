__all__ = [
    "BaseType",
    "SchemaValue",
    "BoolSchema",
    "StringSchema",
    "PathSchema",
]

import pathlib
from typing import Protocol

type BaseType = str | int | float | bool | list | dict


class SchemaValue[T](Protocol):
    """Convert values to and from schema and python."""

    def type_spec(self) -> str:
        """Text to briefly show what valid input values are"""
        ...

    def export_value(self, value: T) -> str | None:
        """Export `value` to valid string representation."""
        ...

    def convert_input(self, input: BaseType) -> T | None:
        """Convert primative to full type."""
        ...


class BoolSchema(SchemaValue[bool]):
    def type_spec(self) -> str:
        return "true | false"

    def export_value(self, value: bool) -> str | None:
        if not isinstance(value, bool):
            return None
        return "true" if value else "false"

    def convert_input(self, input: BaseType) -> bool | None:
        """Convert primative to full type."""
        if not isinstance(input, bool):
            return None
        return input


class StringSchema(SchemaValue[str]):
    def type_spec(self) -> str:
        return '"<string>"'

    def export_value(self, value: str) -> str | None:
        if not isinstance(value, str):
            return None
        return f'"{value}"'

    def convert_input(self, input: BaseType) -> str | None:
        """Convert primative to full type."""
        if not isinstance(input, str):
            return None
        return input


class PathSchema(SchemaValue[pathlib.Path]):
    def type_spec(self) -> str:
        return '"<path>"'

    def export_value(self, value: pathlib.Path) -> str | None:
        if not isinstance(value, pathlib.Path):
            return None
        return f'"{value}"'

    def convert_input(self, input: BaseType) -> pathlib.Path | None:
        """Convert primative to full type."""
        if not isinstance(input, str):
            return None
        return pathlib.Path(input)
