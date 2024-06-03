# TODO: from_spec() does not verify default value is in accordance to metadata

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
            name: str = dataclasses.field(
                default="",
                metadata=metafields.SchemaItemField(
                    possible_values=[schemaspec.StringAdapter()],
                ).metadata(),
            )
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
            default_factory=lambda: SettingsSpec.PredefinedGamesSpec.GameSpec(
                name="guilty_gear_strive"
            ),
            metadata=metafields.SchemaTableField().metadata(),
        )

    games: PredefinedGamesSpec = dataclasses.field(
        default_factory=PredefinedGamesSpec,
        metadata=metafields.SchemaTableField().metadata(),
    )


def test_main():
    res = metafields.schema_from(SettingsSpec)
    res_ns = res.parse_data(
        data={
            "mods_home": "actual/mods/home",
            "alpha": "",
            # "games": {"guilty_gear_strive": {"game_path": True}},
        },
        namespace=SettingsSpec(),
        error_mode=schemaspec.OnConversionError.FAIL,
    )
    div = "=" * 80
    print(div)
    keys = ["games", "default_game.enabled"]
    print(
        res.format_export(
            namespace=res_ns,
            keys=keys,
            use_fullname=False,
            show_help=True,
        )
    )
    print(div)
    print(
        res.format_export(
            namespace=res_ns,
            keys=keys,
            use_fullname=False,
            show_help=False,
        )
    )
    print(div)
    # print(f"Namespace:\n\n{res_ns}")
    # print(div)
    # print(f"Schema help\n{'-'*80}")
    # print(f"{res.help_str()}")
    # print(div)
    # import textwrap
    #
    # wrapper = textwrap.TextWrapper(
    #     tabsize=4,
    #     initial_indent="# ",
    #     subsequent_indent="# ",
    # )
    # text = "blah word" * 30
    # text = wrapper.wrap(text)
    # print(f"{type(text)}")
    # print(text)


if __name__ == "__main__":
    test_main()
