r"""Create `schemaspec.schema.Schema` from dataclasses.

## Example

>>> import schemaspec
>>> @dataclasses.dataclass
... class Foo:
...     item: str = dataclasses.field(
...         default="enabled",
...         metadata=SchemaItemField(
...             possible_values=(schemaspec.StringAdapter(("enabled", "disabled")),),
...         ).metadata(),
...     )
... 
...     @dataclasses.dataclass
...     class Bar:
...         inner: int = dataclasses.field(
...             default=0,
...             metadata=SchemaItemField(
...                 possible_values=(schemaspec.IntAdapter(),),
...             ).metadata(),
...         )
... 
...     bar_table: Bar = dataclasses.field(
...         default_factory=Bar,
...         metadata=SchemaTableField(
...             description="<bar table description>",
...         ).metadata(),
...     )
... 
...     bar_inline: Bar = dataclasses.field(
...         default_factory=Bar,
...         metadata=SchemaItemField(
...             possible_values=(schema_from(Bar),),
...             description="<bar inline description>",
...         ).metadata(),
...     )
>>> foo_schema = schema_from(Foo)
>>> export = foo_schema.format_export(show_help=True)
>>> print(export) #:lang toml
# item = "enabled" | "disabled"
#   Default: "enabled"
item = "enabled"
<BLANKLINE>
# bar_inline = { inner = <integer> }
#   <bar inline description>
#   Default: { inner = 0 }
bar_inline = { inner = 0 }
<BLANKLINE>
[bar_table]
# <bar table description>
<BLANKLINE>
# inner = <integer>
#   Default: 0
inner = 0
"""

__all__ = [
    "SchemaMetaField",
    "SchemaItemField",
    "SchemaTableField",
    "schema_from",
    "METADATA_KEY",
]

import dataclasses
from typing import Protocol, Self

from schemaspec import adapters, schema

METADATA_KEY = "schemaspec"
"""dataclass field metadata key; prevents clashing with other extensions."""


class SchemaMetaField(Protocol):
    """Field within a `dataclasses.Field` metadata helps configures schema."""

    def metadata(self) -> dict[str, Self]:
        """Converts this into a dict to be used in a dataclass field's metadata."""
        return {METADATA_KEY: self}


@dataclasses.dataclass(frozen=True)
class SchemaItemField(SchemaMetaField):
    """Metadata corresponding to `schemaspec.schema.SchemaItem`."""

    possible_values: tuple[adapters.TypeAdapter, ...]
    """Forwarded to `schemaspec.schema.SchemaItem` constructor."""
    description: str | None = None
    """Brief description, forwarded to `schemaspec.schema.SchemaItem` constructor."""


@dataclasses.dataclass(frozen=True)
class SchemaTableField(SchemaMetaField):
    """Metadata corresponding to `schemaspec.schema.SchemaTable`."""

    description: str | None = None
    """Breif description; forwarded to `schemaspec.schema.SchemaTable` constructor."""


def __schema_from[
    T
](cls: type[T], schema_root: schema.SchemaTable[T],) -> schema.SchemaTable[T]:
    """Initialize `schema_root` according to `cls` metadata.

    Sets `cls.__str__(self)` to `schemaspec.schema.Schema.format_export(self)` of the resulting schema.

    :param `cls`: Class whose fields define a schema. Must be a dataclass.
    :param `schema_root`: Schema to be initialized.

    :return `schema_root` after configuration.
    """
    if not dataclasses.is_dataclass(cls):
        raise TypeError(f"{cls} needs to be a dataclass")
    for field in dataclasses.fields(cls):
        data = field.metadata.get(METADATA_KEY, SchemaTableField())
        default_factory = None
        if field.default_factory is not dataclasses.MISSING:
            default_factory = field.default_factory
        elif field.default is not dataclasses.MISSING:
            default_factory = lambda: field.default
        else:
            default_factory = lambda: field.type()
        match data:
            case SchemaItemField():
                schema_root.add_item(
                    name=field.name,
                    possible_values=data.possible_values,
                    default=default_factory(),
                    description=data.description or "",
                )
            case SchemaTableField():
                schema_subtable = schema_root.add_subtable(
                    make_cls=default_factory,
                    name=field.name,
                    description=data.description or "",
                )
                __schema_from(field.type, schema_subtable)
            case _:
                raise ValueError(f"Schema metadata needs to be set")

    def format_str(self) -> str:
        return schema_root.format_export(namespace=self)

    cls.__str__ = format_str
    return schema_root


def schema_from[T](cls: type[T]) -> schema.Schema[T]:
    r"""Create and initialize a `schemaspec.schema.Schema[T]` using `cls` metadata.

    Sets `cls.__str__(self)` to `schemaspec.schema.Schema.format_export(self)` of the resulting schema.

    :param `cls`: Class whose fields define a schema. Must be a dataclass.

    :return: New `schemaspec.schema.Schema[T]` instance.

    >>> foo = 0
    >>> print("local b = 0") #:lang lua
    local b = 0
    """
    schema_root = schema.Schema(make_cls=lambda: cls(), description="")
    __schema_from(cls=cls, schema_root=schema_root)
    return schema_root
