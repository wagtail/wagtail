from .. import Provider as ColorProvider


class Provider(ColorProvider):
    """Implement color provider for ``cs_CZ`` locale."""

    safe_colors = (
        "černá",
        "kaštanová",
        "zelená",
        "námořnická",
        "olivová",
        "fialová",
        "zelenomodrá",
        "limetková",
        "modrá",
        "stříbrná",
        "šedá",
        "žlutá",
        "fuchsiová",
        "aquamarinová",
        "bílá",
    )
