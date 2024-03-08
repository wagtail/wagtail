from collections import OrderedDict

from .. import Provider as ColorProvider

localized = True


class Provider(ColorProvider):
    """Implement color provider for ``id_ID`` locale.

    Sources:
    - https://id.wikipedia.org/wiki/Daftar_warna
    """

    all_colors = OrderedDict(
        (
            ("Abu-abu", "#808080"),
            ("Biru", "#0000FF"),
            ("Biru dongker", "#00008B"),
            ("Biru laut", "#0000CD"),
            ("Biru muda", "#ADD8E6"),
            ("Coklat", "#A52A2A"),
            ("Coklat tua", "#8B4513"),
            ("Emas", "#FFD700"),
            ("Hijau", "#008000"),
            ("Hijau muda", "#90EE90"),
            ("Hijau tua", "#006400"),
            ("Hitam", "#000000"),
            ("Jingga", "#FFA500"),
            ("Kuning", "#FFFF00"),
            ("Koral", "#FF7F50"),
            ("Magenta", "#FF00FF"),
            ("Merah", "#FF0000"),
            ("Merah marun", "#800000"),
            ("Merah jambu", "#FFC0CB"),
            ("Merah bata", "#B22222"),
            ("Perak", "#C0C0C0"),
            ("Nila", "#000080"),
            ("Putih", "#FFFFFF"),
            ("Ungu", "#800080"),
            ("Ungu tua", "#4B0082"),
            ("Zaitun", "#808000"),
        )
    )

    safe_colors = (
        "putih",
        "hitam",
        "merah",
        "hijau",
        "kuning",
        "biru",
        "ungu",
        "abu-abu",
        "coklat",
        "perak",
        "emas",
        "pink",
        "oranye",
    )
