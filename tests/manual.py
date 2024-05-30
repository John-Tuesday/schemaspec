import dataclasses
import pathlib

import schemaspec
from schemaspec import namespace


@dataclasses.dataclass
class SettingsSpec:
    mods_home: pathlib.Path = dataclasses.field(
        default=pathlib.Path("mods/home"),
        metadata=namespace.SchemaItemField(
            possible_values=[schemaspec.PathSchema()],
        ).metadata(),
    )

    @dataclasses.dataclass
    class DefaultGameSpec:
        name: str = dataclasses.field(
            default="Guilty Gear Strive",
            metadata=namespace.SchemaItemField(
                possible_values=[schemaspec.StringSchema()],
            ).metadata(),
        )
        enabled: bool = dataclasses.field(
            default=True,
            metadata=namespace.SchemaItemField(
                possible_values=[schemaspec.BoolSchema()],
            ).metadata(),
        )

    default_game: DefaultGameSpec = dataclasses.field(
        default_factory=DefaultGameSpec,
        metadata=namespace.SchemaTableField().metadata(),
    )

    @dataclasses.dataclass
    class PredefinedGamesSpec:
        @dataclasses.dataclass
        class GameSpec:
            name: str = dataclasses.field(
                metadata=namespace.SchemaItemField(
                    possible_values=[schemaspec.StringSchema()],
                ).metadata(),
            )
            game_path: pathlib.Path = dataclasses.field(
                default=pathlib.Path(
                    "~/.steam/root/steamapps/common/GUILTY GEAR STRIVE/"
                ),
                metadata=namespace.SchemaItemField(
                    possible_values=[
                        schemaspec.PathSchema(),
                    ],
                ).metadata(),
            )

        guilty_gear_strive: GameSpec = dataclasses.field(
            default_factory=lambda: SettingsSpec.PredefinedGamesSpec.GameSpec(
                name="guilty_gear_strive"
            ),
            metadata=namespace.SchemaTableField().metadata(),
        )

    games: PredefinedGamesSpec = dataclasses.field(
        default_factory=PredefinedGamesSpec,
        metadata=namespace.SchemaTableField().metadata(),
    )


def test_main():
    res = namespace.schema_from(SettingsSpec)
    print(f"{res=!s}")
    res_ns = res.parse_data(
        data={"mods_home": "actual/mods/home"},
        namespace=SettingsSpec(),
    )
    div = "=" * 80
    print(div)
    print(f"Namespace:\n\n{res_ns}")
    print(div)


if __name__ == "__main__":
    test_main()
