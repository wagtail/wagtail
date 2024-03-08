from collections import OrderedDict

from .. import Provider as ColorProvider


class Provider(ColorProvider):
    """Implement color provider for ``az_AZ`` locale."""

    all_colors = OrderedDict(
        (
            ("Akuamarin", "#7FFFD4"),
            ("Azure", "#F0FFFF"),
            ("Bej", "#F5F5DC"),
            ("Qara", "#000000"),
            ("Mavi", "#0000FF"),
            ("Mavi-bənövşəyi", "#8A2BE2"),
            ("Qəhvəyi", "#A52A2A"),
            ("Şokolad", "#D2691E"),
            ("Mərcan", "#FF7F50"),
            ("Tünd mavi", "#00008B"),
            ("Tünd boz", "#A9A9A9"),
            ("Tünd yaşıl", "#006400"),
            ("Tünd Xaki", "#BDB76B"),
            ("Tünd Portağal", "#FF8C00"),
            ("Tünd Qırmızı", "#8B0000"),
            ("Tünd Bənövşəyi", "#9400D3"),
            ("Tünd Çəhrayı", "#FF1493"),
            ("Sönük Boz", "#696969"),
            ("Fuksiya", "#FF00FF"),
            ("Qızıl", "#FFD700"),
            ("Boz", "#808080"),
            ("Yaşıl", "#008000"),
            ("Sarı-yaşıl", "#ADFF2F"),
            ("Xaki", "#F0E68C"),
            ("Lavanda çəhrayı", "#FFF0F5"),
            ("Açıq Mavi", "#ADD8E6"),
            ("Açıq Boz", "#D3D3D3"),
            ("Açıq Yaşıl", "#90EE90"),
            ("Açıq Çəhrayı", "#FFB6C1"),
            ("Açıq Sarı", "#FFFFE0"),
            ("Şabalıd", "#800000"),
            ("Portağal", "#FFA500"),
            ("Narıncı Qırmızı", "#FF4500"),
            ("Solğun Yaşıl", "#98FB98"),
            ("Çəhrayı", "#FFC0CB"),
            ("Qırmızı", "#FF0000"),
            ("Aqua", "#2E8B57"),
            ("Gümüş", "#C0C0C0"),
            ("Firuzə", "#40E0D0"),
            ("Bənövşəyi", "#EE82EE"),
            ("Ağ", "#FFFFFF"),
            ("Sarı", "#FFFF00"),
        )
    )

    safe_colors = (
        "qara",
        "tünd qırmızı",
        "yaşıl",
        "zeytun",
        "bənövşəyi",
        "teal",
        "lime",
        "mavi",
        "gümüşü",
        "boz",
        "sarı",
        "fuksiya",
        "ağ",
    )
