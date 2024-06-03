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


def schema_from[
    T: schema.SchemaTable
](cls, schema_root: T = schema.Schema(description="SCHEMA DESCRIPTION"),) -> T:
    """Initialize `schema_root` using metadata in `cls`.

    Sets `cls.__str__()` to `format_export()` of the resulting schema.

    :param `cls`: Class whose fields define a schema.
    :param `schema_root`: The schema parent which will be populated.

    :return: `schema_root` after being configured.
    """
    if not dataclasses.is_dataclass(cls):
        raise TypeError(f"{cls} needs to be a dataclass")
    for field in dataclasses.fields(cls):
        data = field.metadata.get(METADATA_KEY, SchemaTableField())
        default = None
        if field.default is not dataclasses.MISSING:
            default = field.default
        elif field.default_factory is not dataclasses.MISSING:
            default = field.default_factory()
        match data:
            case SchemaItemField():
                schema_root.add_item(
                    name=field.name,
                    possible_values=data.possible_values,
                    default=default,
                    description=data.description or "NO DESCRIPTION",
                )
            case SchemaTableField():
                schema_subtable = schema_root.add_subtable(
                    name=field.name,
                    description=data.description or "NO DESCRIPTION",
                )
                schema_from(field.type, schema_subtable)
            case _:
                raise ValueError(f"Schema metadata needs to be set")
    cls.__str__ = lambda self: schema_root.format_export(self)
    return schema_root
