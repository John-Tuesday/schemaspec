"""Settings/options enforcement and documentation library

Write an option's documentation and dataclass at the same time. Use the library to
enforce constraints, to produce helpful error messages, to generate user-friendly
documentation, or to output default configuration with helpful comments.
"""

from schemaspec.adapters import (
    BaseType,
    BoolAdapter,
    FloatAdapter,
    IntAdapter,
    ListAdapter,
    PathAdapter,
    StringAdapter,
    SubgroupTypeAdapter,
    TypeAdapter,
)
from schemaspec.metafields import (
    METADATA_KEY,
    SchemaItemField,
    SchemaMetaField,
    SchemaTableField,
    schema_from,
)
from schemaspec.schema import (
    Namespace,
    OnConversionError,
    Schema,
    SchemaItem,
    SchemaTable,
)
