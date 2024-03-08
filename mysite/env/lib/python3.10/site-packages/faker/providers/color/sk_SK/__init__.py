from .. import Provider as ColorProvider


class Provider(ColorProvider):
    """Implement color provider for ``sk_SK`` locale."""

    safe_colors = (
        "čierna",
        "gaštanová",
        "zelená",
        "námornícka",
        "olivová",
        "fialová",
        "zelenomodrá",
        "limetková",
        "modrá",
        "strieborná",
        "sivá",
        "žltá",
        "fuchsiová",
        "aquamarinová",
        "biela",
    )
