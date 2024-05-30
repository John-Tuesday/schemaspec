__all__ = [
    "SchemaMetaField",
    "SchemaItemField",
    "SchemaTableField",
    "schema_from",
]

import dataclasses
from typing import Protocol, Self

from schemaspec import schema_table, schema_value

METADATA_KEY = "schemaspec"


class SchemaMetaField(Protocol):
    """Field within a `dataclass.Field.metadata` helps configures schema."""

    def metadata(self) -> dict[str, Self]:
        return {METADATA_KEY: self}


@dataclasses.dataclass
class SchemaItemField(SchemaMetaField):
    """Metadata corresponding to `SchemaItem`"""

    possible_values: list[schema_value.SchemaValue]
    description: str | None = None


@dataclasses.dataclass
class SchemaTableField(SchemaMetaField):
    """Metadata corresponding to `SchemaTable`"""

    description: str | None = None


def schema_from(
    cls,
    schema_root: schema_table.SchemaTable = schema_table.Schema(
        description="SCHEMA DESCRIPTION"
    ),
) -> schema_table.SchemaTable:
    """Create and configure `Schema` according to dataclass and metadata.

    Sets `__str__` in `cls` to `format_export` of the resulting schema.
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
