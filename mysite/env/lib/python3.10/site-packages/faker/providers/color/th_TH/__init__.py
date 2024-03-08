from collections import OrderedDict

from .. import Provider as ColorProvider

localized = True


class Provider(ColorProvider):
    """Implement color provider for ``th_TH`` locale.

    Sources:
    - https://th.wikipedia.org/wiki/รายชื่อสี
    """

    all_colors = OrderedDict(
        (
            ("สีดำ", "#000000"),
            ("สีน้ำเงินเขียว", "#0095B6"),
            ("สีน้ำเงินม่วง", "#8A2BE2"),
            ("สีทองแดง", "#CD7F32"),
            ("สีน้ำตาล", "#964B00"),
            ("สีกาแฟ", "#6F4E37"),
            ("สีทอง", "#FFD700"),
            ("สีเทา", "#808080"),
            ("สีเขียว", "#00FF00"),
            ("สีหยก", "#00A86B"),
            ("สีส้ม", "#FFA500"),
            ("สีส้มแดง", "#FF4500"),
            ("สีออร์คิด", "#DA70D6"),
            ("สีชมพู", "#FFC0CB"),
            ("สีม่วง", "#800080"),
            ("สีแดง", "#FF0000"),
            ("สีเงิน", "#C0C0C0"),
            ("สีขาว", "#FFFFFF"),
            ("สีเหลือง", "#FFFF00"),
        )
    )

    safe_colors = (
        "สีดำ",
        "สีน้ำตาล",
        "สีทอง",
        "สีเขียว",
        "สีส้ม",
        "สีชมพู",
        "สีม่วง",
        "สีเงิน",
        "สีแดง",
        "สีเงิน",
        "สีขาว",
        "สีเหลือง",
    )
