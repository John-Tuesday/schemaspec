import dataclasses
import pathlib

import schemaspec
from schemaspec import metafields


@dataclasses.dataclass
class SettingsSpec:
    mods_home: pathlib.Path = dataclasses.field(
        default=pathlib.Path("mods/home"),
        metadata=metafields.SchemaItemField(
            possible_values=[schemaspec.PathAdapter()],
        ).metadata(),
    )

    alpha: str = dataclasses.field(
        default="enabled",
        metadata=metafields.SchemaItemField(
            possible_values=[schemaspec.StringAdapter()],
            description="blurd blahd\nbloo blow\n" + ("word " * 30),
        ).metadata(),
    )

    @dataclasses.dataclass
    class DefaultGameSpec:
        name: str = dataclasses.field(
            default="Guilty Gear Strive",
            metadata=metafields.SchemaItemField(
                possible_values=[schemaspec.StringAdapter()],
            ).metadata(),
        )
        enabled: bool = dataclasses.field(
            default=True,
            metadata=metafields.SchemaItemField(
                possible_values=[schemaspec.BoolAdapter()],
            ).metadata(),
        )

    default_game: DefaultGameSpec = dataclasses.field(
        default_factory=DefaultGameSpec,
        metadata=metafields.SchemaTableField().metadata(),
    )

    @dataclasses.dataclass
    class PredefinedGamesSpec:
        @dataclasses.dataclass
        class GameSpec:
            game_path: pathlib.Path = dataclasses.field(
                default=pathlib.Path(
                    "~/.steam/root/steamapps/common/GUILTY GEAR STRIVE/"
                ),
                metadata=metafields.SchemaItemField(
                    possible_values=[
                        schemaspec.BoolAdapter(choices=(False,)),
                        schemaspec.PathAdapter(),
                    ],
                ).metadata(),
            )

        guilty_gear_strive: GameSpec = dataclasses.field(
            default_factory=GameSpec,
            metadata=metafields.SchemaTableField().metadata(),
        )

    games: PredefinedGamesSpec = dataclasses.field(
        default_factory=PredefinedGamesSpec,
        metadata=metafields.SchemaTableField().metadata(),
    )

    inline_test: PredefinedGamesSpec = dataclasses.field(
        default_factory=lambda x=PredefinedGamesSpec: x(
            guilty_gear_strive=x.GameSpec(pathlib.Path("alt/default"))
        ),
        metadata=metafields.SchemaItemField(
            possible_values=[
                schemaspec.BoolAdapter(),
                metafields.schema_from(PredefinedGamesSpec),
            ],
        ).metadata(),
    )

    alt_test: PredefinedGamesSpec = dataclasses.field(
        default_factory=lambda x=PredefinedGamesSpec: x(
            guilty_gear_strive=x.GameSpec(pathlib.Path("alt/default"))
        ),
        metadata=metafields.SchemaTableField().metadata(),
    )


def test_main():
    settings_schema = metafields.schema_from(SettingsSpec)
    settings = settings_schema.parse_data(
        data={
            "mods_home": "actual/mods/home",
        },
        namespace=SettingsSpec(),
        error_mode=schemaspec.OnConversionError.FAIL,
    )
    div = "=" * 80
    print(div)
    print(settings_schema)
    print(div)
    print(settings)
    print(div)
    print(settings_schema.format_export(namespace=settings, show_help=True))
    print(div)


if __name__ == "__main__":
    test_main()
