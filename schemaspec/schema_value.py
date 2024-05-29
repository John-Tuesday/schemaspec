__all__ = [
    "BaseType",
    "SchemaValue",
]

import pathlib
from typing import Callable, Optional

type BaseType = str | int | float | bool | list | dict


class SchemaValue[T]:
    """Possible value for a schema item.

    Converts to and from schema known types, i.e. BaseType.
    Outputs schema documentation string.

    Attributes:
        export_doc:
            String representation in schema documentation, i.e. VALUE in
                `option = VALUE`
        export_value:
            Callable which receives an instance of T and returns a string which
            is a valid toml value and results in an identical instance of T
            after parsing and converting input, otherwise returns None.
        convert_input:
            Callable which converts a basic parsed toml-value to an instance of
            T or return None if not possible.
    """

    def __init__(
        self,
        export_doc: str,
        export_value: Callable[[T], Optional[str]],
        convert_input: Callable[[BaseType], Optional[T]],
    ):
        self.export_doc = export_doc
        self.export_value = export_value
        self.convert_input = convert_input

    @staticmethod
    def export_bool(value: bool) -> str | None:
        if not isinstance(value, bool):
            return None
        return "true" if value else "false"

    @staticmethod
    def convert_bool(input: BaseType) -> bool | None:
        if not isinstance(input, bool):
            return None
        return input

    @staticmethod
    def bool_schema() -> "SchemaValue":
        return SchemaValue(
            export_doc="true | false",
            export_value=SchemaValue.export_bool,
            convert_input=SchemaValue.convert_bool,
        )

    @staticmethod
    def export_str(value: str) -> str | None:
        if not isinstance(value, str):
            return None
        return f'"{value}"'

    @staticmethod
    def convert_str(input: BaseType) -> str | None:
        if not isinstance(input, str):
            return None
        return input

    @staticmethod
    def str_schema() -> "SchemaValue":
        return SchemaValue(
            export_doc='"<string>"',
            export_value=SchemaValue.export_str,
            convert_input=SchemaValue.convert_str,
        )

    @staticmethod
    def export_path(path: pathlib.Path) -> str:
        """Return path surrounded in double-quotes."""
        return f'"{path}"'

    @staticmethod
    def convert_path(input: BaseType) -> pathlib.Path:
        """Convert input to a path or raise an exception."""
        if isinstance(input, str):
            return pathlib.Path(input)
        raise Exception("input type needs to be string")

    @staticmethod
    def path_schema() -> "SchemaValue":
        """Create a new schema value which expects path input/output."""
        return SchemaValue(
            export_doc='"<path>"',
            export_value=SchemaValue.export_path,
            convert_input=SchemaValue.convert_path,
        )
