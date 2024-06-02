"""Schema builders and nestable units.
"""

__all__ = [
    "Schema",
    "SchemaItem",
    "SchemaTable",
    "Namespace",
]

import dataclasses
import pathlib
import tomllib
from typing import Any, Callable, Optional

from schemaspec import schema_value


class Namespace:
    """Simple class used by `SchemaTable.parse_data()` to hold attributes and return."""

    def __init__(self, formatter: Optional[Callable[[Any], str]] = None):
        self.__formatter = formatter if formatter else lambda x: f"{vars(x)}"

    def __str__(self) -> str:
        return self.__formatter(self)


@dataclasses.dataclass
class SchemaItem[T]:
    """Option in a schema.

    Attributes:
        short_name: Name of this option, excluding any parent tables.
        possible_values: Un order of priority, a list of value schema.
        default_value: Value to be used if none is specified.
        description: Summary of what is being configured. Appears in help_str()
    """

    short_name: str
    possible_values: list[schema_value.SchemaValue]
    default_value: T
    description: str

    def export_value(self, value: T) -> str | None:
        """Convert value to a valid toml-value.

        Tries to convert `value` with each possible_values; returns the first
        valid result.

        Returns:
            A valid toml-value or None if it is not possible.
        """
        for schema_v in self.possible_values:
            v = schema_v.export_value(value)
            if v is not None:
                return v
        return None

    def convert_input(self, input: schema_value.BaseType) -> T | None:
        """Convert input to an instance of T."""
        for schema_v in self.possible_values:
            v = schema_v.convert_input(input)
            if v is not None:
                return v
        return None

    def usage_str(self) -> str:
        """Return, as a string, the usage help."""
        v = " | ".join([x.type_spec() for x in self.possible_values])
        return f"{self.short_name} = {v}"

    def help_str(self, tab: str = "  ") -> str:
        """Return summary of this value's purpose and usage, and default value."""
        s = f"\n{tab}".join(
            [
                self.usage_str(),
                self.description,
                f"Default: {self.export_value(self.default_value)}",
            ]
        )
        return s


class SchemaTable:
    """Table of key-value options and optionally subtables."""

    def __init__(self, full_name: str, description: str = ""):
        """Create a new (sub)table.

        :param `full_name`: Toml-compliant name of this table, i.e. 'parent.child' An
            emtpy string indicates the table to Top-Level.
        :param `description`: Summary of this table. Will be displayed in `help_str()`.
        """
        self.__full_name = full_name
        self.__description = description
        self.__data = {}
        self.__subtables = {}

    def add_item(
        self,
        name: str,
        possible_values: list[schema_value.SchemaValue],
        default,
        description: str,
    ) -> None:
        """Add schema item."""
        self.__data[name] = SchemaItem(
            short_name=name,
            possible_values=possible_values,
            default_value=default,
            description=description,
        )

    def add_subtable(
        self,
        name: str,
        description: str,
    ) -> "SchemaTable":
        """Create a table within this table and return it."""
        table = SchemaTable(
            full_name=f"{self.__full_name}.{name}" if self.__full_name else f"{name}",
            description=description,
        )
        self.__subtables[name] = table
        return table

    def help_str(self, level: int = 0) -> str:
        """Return a string providing schema description and usage information.

        :param `level`: The number of parents of this table. Currently unused.
        """
        s = []
        top_str = [f"[{self.__full_name}]"] if self.__full_name else []
        if self.__description:
            top_str.append(self.__description)
        top_str = "\n".join(top_str)
        if top_str:
            s.append(top_str)
        vals = "\n".join([x.help_str() for x in self.__data.values()])
        if vals:
            s.append(vals)
        subs = "\n\n".join(
            [x.help_str(level=level + 1) for x in self.__subtables.values()]
        )
        if subs:
            s.append(subs)
        return "\n\n".join(s)

    def parse_data[
        T: Any
    ](self, data: dict[str, schema_value.BaseType], namespace: T,) -> T:
        """ "Convert data to objects and assign them as attributes of namespace.

        All items defined in `data` will overwrite the corresponding attribute in
        `namespace`. If niether `data` nor `namespace` define an item, then and only then,
        the attribute in namespace will be set to `schema.default`.

        :param `data`: Map-like object representing basic parsed output, e.g. the output
            of `tomllib.load()`
        :param `namespace`: Namespace-like object whose attributes will be set according
            to schema.

        :return: Populated `namespace`.

        :raises: `Exception` if unexpected key in `data` or expected child of `data` to
            be dict-like.
        """
        for key, schema in self.__data.items():
            if key in data:
                value = data.pop(key)
                setattr(namespace, key, schema.convert_input(value))
            elif not hasattr(namespace, key):
                setattr(namespace, key, schema.default_value)
        for key, subtable in self.__subtables.items():
            subdata = data.pop(key, {})
            if not isinstance(subdata, dict):
                raise Exception(f'Schema expects table (dic) "{subtable.__full_name}"')
            subspace = getattr(namespace, key, Namespace(self.format_export))
            setattr(namespace, key, subtable.parse_data(subdata, namespace=subspace))
        if len(data) > 0:
            raise Exception(f"Unexpected keys")
        return namespace

    def format_export_keys(
        self,
        namespace: Any,
        *keys: str,
        use_fullname: bool = False,
    ) -> str:
        """Format namespace attributes given by keys according to schema.

        :param `namespace`: Namespace-like object whose attributes are the parsed result
            of a configuration file.
        :param `keys`: Sequence of strings specifying children to include. Nested
            children are seperated with a dot `'.'`, but *be cautious* as there is no way
            to escape the dot ... *yet*.
        :param `use_fullname`: Toggle if output specifies keys using dot notation or
            table headers.

        :return: A valid toml string representing values of namespace at keys.
        """
        if not keys:
            return self.format_export(namespace=namespace)
        vals = [f"[{self.__full_name}]"] if use_fullname and self.__full_name else []
        tables = []
        for key in keys:
            child_keys = key.split(".", maxsplit=1)
            root_key = child_keys.pop(0)
            if root_key in self.__data:
                schema = self.__data[root_key]
                rhs = schema.export_value(getattr(namespace, root_key))
                lhs = (
                    f"{self.__full_name}.{schema.short_name}"
                    if use_fullname and self.__full_name
                    else f"{schema.short_name}"
                )
                vals.append(f"{lhs} = {rhs}")
            elif root_key in self.__subtables:
                subtable_schema = self.__subtables[root_key]
                subtable_ns = getattr(namespace, root_key)
                tables.append(
                    subtable_schema.format_export_keys(
                        subtable_ns,
                        *child_keys,
                        use_fullname=use_fullname,
                    )
                )
            else:
                raise Exception("key not found in schema")
        if vals:
            tables.insert(0, "\n".join(vals))
        return "\n\n".join(tables)

    def format_export(self, namespace: Any) -> str:
        """Format namespace according to schema.

        *Functionally equivalent to `format_export_keys()` but with fewer options.*

        Keys in defined in `self` must match with attributes in `namespace`, except
        extra attributes or keys in `namespace` are ignored.

        :return: Convert `namespace` to a valid toml file.
        """
        header = f"[{self.__full_name}]\n" if self.__full_name else ""
        vals = []
        for key, schema in self.__data.items():
            v = schema.export_value(getattr(namespace, key))
            vals.append(f"{key} = {v}")
        tables = ["\n".join(vals)] if vals else []
        for key, subtable in self.__subtables.items():
            v = subtable.format_export(getattr(namespace, key))
            tables.append(v)
        return f"{header}{"\n\n".join(tables)}"

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}"
            f"(full_name={self.__full_name!r}, description={self.__description!r})"
        )

    def __str__(self) -> str:
        return self.help_str()


class Schema(SchemaTable):
    """Schema root; defines and pretty prints configuration options."""

    def __init__(self, description: str):
        """Create new instance, with description."""
        super().__init__(full_name="", description=description)

    def load_toml[
        T
    ](self, filepath: pathlib.Path, namespace: T,) -> T:
        """Load `filepath` as toml and send output to `parse_data()`."""
        with open(filepath, "rb") as f:
            data = tomllib.load(f)
        return self.parse_data(data, namespace=namespace)
