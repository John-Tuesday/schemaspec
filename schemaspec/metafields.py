"""Create `schemaspec.schema.Schema` from dataclasses.
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


@dataclasses.dataclass
class SchemaItemField(SchemaMetaField):
    """Metadata corresponding to `schemaspec.schema.SchemaItem`."""

    possible_values: list[adapters.TypeAdapter]
    description: str | None = None


@dataclasses.dataclass
class SchemaTableField(SchemaMetaField):
    """Metadata corresponding to `schemaspec.schema.SchemaTable`."""

    description: str | None = None


def __schema_from[
    T
](cls: type[T], schema_root: schema.SchemaTable[T],) -> schema.SchemaTable[T]:
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
    cls.__str__ = lambda self: schema_root.format_export(self)
    return schema_root


def schema_from[T](cls: type[T]) -> schema.Schema[T]:
    """Create and initialize a `schemaspec.schema.Schema[T]` using `cls` metadata.

    Sets `cls.__str__(self)` to `schemaspec.schema.Schema.format_export(self)` of the resulting schema.

    :param `cls`: Class whose fields define a schema. Must be a dataclass.

    :return New `schemaspec.schema.Schema[T]` instance.
    """
    schema_root = schema.Schema(make_cls=lambda: cls(), description="")
    __schema_from(cls=cls, schema_root=schema_root)
    return schema_root
