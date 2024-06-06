"""Schema builders and nestable units.
"""

__all__ = [
    "OnConversionError",
    "Schema",
    "SchemaItem",
    "SchemaTable",
]

import dataclasses
import enum
import itertools
import pathlib
import textwrap
import tomllib
from typing import Any, Callable, Optional, override

from schemaspec import adapters


@dataclasses.dataclass(frozen=True)
class SchemaItem[T]:
    """Key-value schema. Smallest whole unit of a `Schema`"""

    short_name: str
    """Name of this option, excluding any parent tables."""
    possible_values: list[adapters.TypeAdapter]
    """Un order of priority, a list of value schema."""
    default_value: T
    """Value to be used if none is specified."""
    description: str
    """Summary of what is being configured. Appears in `help_str()`."""
    type_spec: str = dataclasses.field(init=False)
    """Combined types from `possible_values`"""
    default_input: str = dataclasses.field(init=False)
    """Exported `default_value`."""
    help_str: str = dataclasses.field(init=False)
    """Summary details of this item's possibilities and constraints."""

    def __post_init__(self):
        object.__setattr__(
            self,
            "type_spec",
            " | ".join(
                [x.type_spec for x in self.possible_values],
            ),
        )
        temp = self.export(self.default_value)
        if temp is None:
            raise ValueError("Default value cannot be exported.")
        object.__setattr__(self, "default_input", temp)
        sects = []
        wrapper = textwrap.TextWrapper(tabsize=4)
        desc = "\n".join(map(wrapper.fill, self.description.split("\n\n")))
        if desc:
            sects.append(desc)
        sects.append(f"Default: {self.default_input}")
        usage = f"{self.short_name} = {self.type_spec}"
        object.__setattr__(
            self,
            "help_str",
            f"{usage}\n{textwrap.indent("\n".join(sects), "  ")}",
        )

    def is_valid(self, value: T) -> bool:
        for adapter in self.possible_values:
            if adapter.is_valid(value):
                return True
        return False

    def export(self, value: T) -> str | None:
        """Convert `value` to a valid schema-value.

        Tries to convert `value` with each `possible_values`; returns the first
        valid result.

        :return: Value as a schema string or None if it is not possible.
        """
        for schema_v in self.possible_values:
            v = schema_v.export(value)
            if v is not None:
                return v
        return None

    def convert(self, value: adapters.BaseType) -> T | None:
        """Convert from schema-primative `input` to full internal type `T`.

        :return: A new instance of `T`, or None if it cannot be done.
        """
        for schema_v in self.possible_values:
            v = schema_v.convert(value)
            if v is not None:
                return v
        return None


class OnConversionError(enum.Enum):
    """Action to take when `SchemaTable.parse_data()` fails to convert input value."""

    IGNORE = enum.auto()
    """Do nothing."""
    SET_NONE = enum.auto()
    """Set the value to `None`."""
    SET_DEFAULT = enum.auto()
    """Set the value to the corresponding schema default."""
    REMOVE = enum.auto()
    """Delete attribute if it existed, otherwise do nothing."""
    FAIL = enum.auto()
    """Raise an error."""


class SchemaTable[R](adapters.TypeAdapter[R]):
    """Table of key-value options and optionally subtables."""

    def __init__(
        self,
        make_cls: Callable[[], R],
        full_name: str,
        description: str,
    ):
        """Create a new (sub)table.

        :param `full_name`: Toml-compliant name of this table, i.e. 'parent.child' An
            emtpy string indicates the table to Top-Level.
        :param `description`: Summary of this table. Will be displayed in `help_str()`.
        """
        self.__fullname = full_name
        self.__description = description
        self.__items: dict[str, SchemaItem] = {}
        self.__subtables: dict[str, SchemaTable] = {}
        self.__make_cls: Callable[[], R] = make_cls

    def _fullname_of(self, name: str) -> str:
        return f"{self.__fullname}.{name}" if self.__fullname else name

    def add_item(
        self,
        name: str,
        possible_values: list[adapters.TypeAdapter],
        default,
        description: str,
    ) -> None:
        """Add schema item."""
        self.__items[name] = SchemaItem(
            short_name=name,
            possible_values=possible_values,
            default_value=default,
            description=description,
        )

    def add_subtable[
        T
    ](
        self,
        make_cls: Callable[[], T],
        name: str,
        description: str,
    ) -> "SchemaTable[T]":
        """Create a table within this table and return it."""
        table = SchemaTable(
            make_cls=make_cls,
            full_name=self._fullname_of(name),
            description=description,
        )
        self.__subtables[name] = table
        return table

    def help_str(self) -> str:
        """Return a string providing schema description and usage information."""
        header = f"[{self.__fullname}]\n" if self.__fullname else ""
        if self.__description:
            header = f"{header}{self.__description}\n\n"
        vals = "\n".join([x.help_str for x in self.__items.values()])
        subs = "\n\n".join([x.help_str() for x in self.__subtables.values()])
        return f"{header}{"\n\n".join([x for x in [vals, subs] if x])}"

    def parse_data(
        self,
        data: dict[str, adapters.BaseType],
        namespace: Optional[R] = None,
        error_mode: OnConversionError = OnConversionError.FAIL,
    ) -> R:
        """ "Convert data to objects and assign them as attributes of namespace.

        All items defined in `data` will overwrite the corresponding attribute in
        `namespace`. If niether `data` nor `namespace` define an item, then and only then,
        the attribute in namespace will be set to `schema.default`.

        :param `data`: Map-like object representing basic parsed output, e.g. the output
            of `tomllib.load()`
        :param `namespace`: Namespace-like object whose attributes will be set according
            to schema.

        :return: Populated `namespace`.

        :raises: `KeyError` if unexpected key in `data`
        :raises: `TypeError` if expected child of `data` to be dict-like.
        :raises: `ValueError` if a schema-value cannot be converted to its full type,
            and `error_mode` is `OnConversionError.FAIL`.
        """
        if namespace is None:
            namespace = self.__make_cls()
        for key, schema in self.__items.items():
            if key in data:
                value = data.pop(key)
                result = schema.convert(value)
                if result is not None:
                    setattr(namespace, key, result)
                    continue
                match error_mode:
                    case OnConversionError.FAIL:
                        msg = (
                            f"{schema.short_name} in {self.__fullname or "root"} table"
                            f" cannot convert '{value!r}' to an appropriate value.\n"
                            f"\nHelp:\n{schema.help_str}"
                        )
                        raise ValueError(msg)
                    case OnConversionError.IGNORE:
                        continue
                    case OnConversionError.REMOVE if hasattr(namespace, key):
                        delattr(namespace, key)
                    case OnConversionError.SET_DEFAULT:
                        setattr(namespace, key, schema.default_value)
                    case OnConversionError.SET_NONE:
                        setattr(namespace, key, None)
            elif not hasattr(namespace, key):
                setattr(namespace, key, schema.default_value)
        for key, subtable in self.__subtables.items():
            subdata = data.pop(key, {})
            if not isinstance(subdata, dict):
                raise TypeError(f'Schema expects table (dic) "{subtable.__fullname}"')
            subspace = getattr(namespace, key, subtable.__make_cls())
            setattr(
                namespace,
                key,
                subtable.parse_data(subdata, namespace=subspace, error_mode=error_mode),
            )
        if len(data) > 0:
            raise KeyError(f"Unexpected keys")
        return namespace

    def format_export(
        self,
        namespace: Any,
        keys: list[str] = [],
        use_fullname: bool = False,
        show_help: bool = False,
    ) -> str:
        """Format namespace attributes given by keys according to schema.

        :param `namespace`: Namespace-like object whose attributes are the parsed result
            of a configuration file.
        :param `keys`: Sequence of strings specifying children to include. Leave it
            empty to include all children. Nested children are seperated with a dot
            `'.'`, but *be cautious* as there is no way to escape the dot ... *yet*.
        :param `use_fullname`: Toggle if output specifies keys using dot notation or
            table headers.
        :param `show_help`: Include help texts as comments.

        :return: A valid toml string representing values of namespace at keys.

        :raises: `KeyError` if a key from `keys` cannot be found in this schema.
        """
        header = ""
        if not use_fullname and self.__fullname:
            header = f"[{self.__fullname}]\n"
        if show_help and self.__description:
            desc = textwrap.fill(
                self.__description,
                initial_indent="# ",
                subsequent_indent="# ",
            )
            header = f"{header}{desc}\n\n"
        vals = []
        tables = []
        for key in keys or itertools.chain(
            self.__items.keys(), self.__subtables.keys()
        ):
            child_keys = key.split(".", maxsplit=1)
            root_key = child_keys.pop(0)
            if root_key in self.__items:
                schema = self.__items[root_key]
                rhs = schema.export(getattr(namespace, root_key))
                lhs = (
                    self._fullname_of(schema.short_name)
                    if use_fullname
                    else schema.short_name
                )
                val = f"{lhs} = {rhs}"
                if show_help:
                    help_text = textwrap.indent(schema.help_str, "# ", lambda _: True)
                    val = f"{help_text}\n{val}"
                vals.append(val)
            elif root_key in self.__subtables:
                subtable_schema = self.__subtables[root_key]
                subtable_ns = getattr(namespace, root_key)
                tables.append(
                    subtable_schema.format_export(
                        namespace=subtable_ns,
                        keys=child_keys,
                        use_fullname=use_fullname,
                        show_help=show_help,
                    )
                )
            else:
                raise KeyError(f"Schema does not have a child '{root_key}'.")
        if vals:
            tables.insert(0, ("\n\n" if show_help else "\n").join(vals))
        return f"{header}{"\n\n".join(tables)}"

    @property
    @override
    def type_spec(self) -> str:
        l = [
            f"{k} = {v.type_spec}"
            for k, v in itertools.chain(self.__items.items(), self.__subtables.items())
        ]
        return f"{{ {", ".join(l)} }}"

    @override
    def is_valid(self, value: R) -> bool:
        attrs = {k: v for k, v in vars(value) if not k.startswith("_")}
        for key, adapter in itertools.chain(
            self.__items.items(), self.__subtables.items()
        ):
            if key not in attrs:
                return False
            if not adapter.is_valid(attrs.pop(key)):
                return False
        return len(attrs) == 0

    @override
    def export(self, value: R) -> str | None:
        l = [
            f"{k} = {v.export(getattr(value, k))}"
            for k, v in itertools.chain(self.__items.items(), self.__subtables.items())
        ]
        return f"{{ {", ".join(l)} }}"

    @override
    def convert(self, value: adapters.BaseType) -> R | None:
        if not isinstance(value, dict):
            return None
        return self.parse_data(data=value, namespace=self.__make_cls())

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}"
            f"(full_name={self.__fullname!r}, description={self.__description!r})"
        )

    def __str__(self) -> str:
        return self.help_str()


class Schema[R](SchemaTable[R]):
    """Schema root; defines and pretty prints configuration options."""

    def __init__(self, make_cls: Callable[[], R], description: str):
        """Create new instance, with description."""
        super().__init__(make_cls=make_cls, full_name="", description=description)

    def load_toml(
        self,
        filepath: pathlib.Path,
        namespace: Optional[R] = None,
    ) -> R:
        """Load `filepath` as toml and send output to `parse_data()`."""
        with open(filepath, "rb") as f:
            data = tomllib.load(f)
        return self.parse_data(data, namespace=namespace)
