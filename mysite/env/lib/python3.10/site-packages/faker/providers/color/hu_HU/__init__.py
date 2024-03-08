from .. import Provider as ColorProvider


class Provider(ColorProvider):
    """Implement color provider for ``hu_HU`` locale."""

    safe_colors = (
        "fekete",
        "bordó",
        "zöld",
        "királykék",
        "oliva",
        "bíbor",
        "kékeszöld",
        "citromzöld",
        "kék",
        "ezüst",
        "szürke",
        "sárga",
        "mályva",
        "akvamarin",
        "fehér",
    )
