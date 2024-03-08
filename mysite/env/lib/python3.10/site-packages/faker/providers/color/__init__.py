from collections import OrderedDict
from functools import cached_property
from typing import Dict, Optional, Tuple

from ...typing import HueType
from .. import BaseProvider, ElementsType
from .color import RandomColor

localized = True


class Provider(BaseProvider):
    """Implement default color provider for Faker."""

    all_colors: Dict[str, str] = OrderedDict(
        (
            ("AliceBlue", "#F0F8FF"),
            ("AntiqueWhite", "#FAEBD7"),
            ("Aqua", "#00FFFF"),
            ("Aquamarine", "#7FFFD4"),
            ("Azure", "#F0FFFF"),
            ("Beige", "#F5F5DC"),
            ("Bisque", "#FFE4C4"),
            ("Black", "#000000"),
            ("BlanchedAlmond", "#FFEBCD"),
            ("Blue", "#0000FF"),
            ("BlueViolet", "#8A2BE2"),
            ("Brown", "#A52A2A"),
            ("BurlyWood", "#DEB887"),
            ("CadetBlue", "#5F9EA0"),
            ("Chartreuse", "#7FFF00"),
            ("Chocolate", "#D2691E"),
            ("Coral", "#FF7F50"),
            ("CornflowerBlue", "#6495ED"),
            ("Cornsilk", "#FFF8DC"),
            ("Crimson", "#DC143C"),
            ("Cyan", "#00FFFF"),
            ("DarkBlue", "#00008B"),
            ("DarkCyan", "#008B8B"),
            ("DarkGoldenRod", "#B8860B"),
            ("DarkGray", "#A9A9A9"),
            ("DarkGreen", "#006400"),
            ("DarkKhaki", "#BDB76B"),
            ("DarkMagenta", "#8B008B"),
            ("DarkOliveGreen", "#556B2F"),
            ("DarkOrange", "#FF8C00"),
            ("DarkOrchid", "#9932CC"),
            ("DarkRed", "#8B0000"),
            ("DarkSalmon", "#E9967A"),
            ("DarkSeaGreen", "#8FBC8F"),
            ("DarkSlateBlue", "#483D8B"),
            ("DarkSlateGray", "#2F4F4F"),
            ("DarkTurquoise", "#00CED1"),
            ("DarkViolet", "#9400D3"),
            ("DeepPink", "#FF1493"),
            ("DeepSkyBlue", "#00BFFF"),
            ("DimGray", "#696969"),
            ("DodgerBlue", "#1E90FF"),
            ("FireBrick", "#B22222"),
            ("FloralWhite", "#FFFAF0"),
            ("ForestGreen", "#228B22"),
            ("Fuchsia", "#FF00FF"),
            ("Gainsboro", "#DCDCDC"),
            ("GhostWhite", "#F8F8FF"),
            ("Gold", "#FFD700"),
            ("GoldenRod", "#DAA520"),
            ("Gray", "#808080"),
            ("Green", "#008000"),
            ("GreenYellow", "#ADFF2F"),
            ("HoneyDew", "#F0FFF0"),
            ("HotPink", "#FF69B4"),
            ("IndianRed", "#CD5C5C"),
            ("Indigo", "#4B0082"),
            ("Ivory", "#FFFFF0"),
            ("Khaki", "#F0E68C"),
            ("Lavender", "#E6E6FA"),
            ("LavenderBlush", "#FFF0F5"),
            ("LawnGreen", "#7CFC00"),
            ("LemonChiffon", "#FFFACD"),
            ("LightBlue", "#ADD8E6"),
            ("LightCoral", "#F08080"),
            ("LightCyan", "#E0FFFF"),
            ("LightGoldenRodYellow", "#FAFAD2"),
            ("LightGray", "#D3D3D3"),
            ("LightGreen", "#90EE90"),
            ("LightPink", "#FFB6C1"),
            ("LightSalmon", "#FFA07A"),
            ("LightSeaGreen", "#20B2AA"),
            ("LightSkyBlue", "#87CEFA"),
            ("LightSlateGray", "#778899"),
            ("LightSteelBlue", "#B0C4DE"),
            ("LightYellow", "#FFFFE0"),
            ("Lime", "#00FF00"),
            ("LimeGreen", "#32CD32"),
            ("Linen", "#FAF0E6"),
            ("Magenta", "#FF00FF"),
            ("Maroon", "#800000"),
            ("MediumAquaMarine", "#66CDAA"),
            ("MediumBlue", "#0000CD"),
            ("MediumOrchid", "#BA55D3"),
            ("MediumPurple", "#9370DB"),
            ("MediumSeaGreen", "#3CB371"),
            ("MediumSlateBlue", "#7B68EE"),
            ("MediumSpringGreen", "#00FA9A"),
            ("MediumTurquoise", "#48D1CC"),
            ("MediumVioletRed", "#C71585"),
            ("MidnightBlue", "#191970"),
            ("MintCream", "#F5FFFA"),
            ("MistyRose", "#FFE4E1"),
            ("Moccasin", "#FFE4B5"),
            ("NavajoWhite", "#FFDEAD"),
            ("Navy", "#000080"),
            ("OldLace", "#FDF5E6"),
            ("Olive", "#808000"),
            ("OliveDrab", "#6B8E23"),
            ("Orange", "#FFA500"),
            ("OrangeRed", "#FF4500"),
            ("Orchid", "#DA70D6"),
            ("PaleGoldenRod", "#EEE8AA"),
            ("PaleGreen", "#98FB98"),
            ("PaleTurquoise", "#AFEEEE"),
            ("PaleVioletRed", "#DB7093"),
            ("PapayaWhip", "#FFEFD5"),
            ("PeachPuff", "#FFDAB9"),
            ("Peru", "#CD853F"),
            ("Pink", "#FFC0CB"),
            ("Plum", "#DDA0DD"),
            ("PowderBlue", "#B0E0E6"),
            ("Purple", "#800080"),
            ("Red", "#FF0000"),
            ("RosyBrown", "#BC8F8F"),
            ("RoyalBlue", "#4169E1"),
            ("SaddleBrown", "#8B4513"),
            ("Salmon", "#FA8072"),
            ("SandyBrown", "#F4A460"),
            ("SeaGreen", "#2E8B57"),
            ("SeaShell", "#FFF5EE"),
            ("Sienna", "#A0522D"),
            ("Silver", "#C0C0C0"),
            ("SkyBlue", "#87CEEB"),
            ("SlateBlue", "#6A5ACD"),
            ("SlateGray", "#708090"),
            ("Snow", "#FFFAFA"),
            ("SpringGreen", "#00FF7F"),
            ("SteelBlue", "#4682B4"),
            ("Tan", "#D2B48C"),
            ("Teal", "#008080"),
            ("Thistle", "#D8BFD8"),
            ("Tomato", "#FF6347"),
            ("Turquoise", "#40E0D0"),
            ("Violet", "#EE82EE"),
            ("Wheat", "#F5DEB3"),
            ("White", "#FFFFFF"),
            ("WhiteSmoke", "#F5F5F5"),
            ("Yellow", "#FFFF00"),
            ("YellowGreen", "#9ACD32"),
        )
    )

    safe_colors: ElementsType[str] = (
        "black",
        "maroon",
        "green",
        "navy",
        "olive",
        "purple",
        "teal",
        "lime",
        "blue",
        "silver",
        "gray",
        "yellow",
        "fuchsia",
        "aqua",
        "white",
    )

    def color_name(self) -> str:
        """Generate a color name."""
        return self.random_element(self.all_colors.keys())

    def safe_color_name(self) -> str:
        """Generate a web-safe color name."""
        return self.random_element(self.safe_colors)

    def hex_color(self) -> str:
        """Generate a color formatted as a hex triplet."""
        return f"#{self.random_int(1, 16777215):06x}"

    def safe_hex_color(self) -> str:
        """Generate a web-safe color formatted as a hex triplet."""
        return f"#{self.random_int(0, 15) * 17:02x}{self.random_int(0, 15) * 17:02x}{self.random_int(0, 15) * 17:02x}"

    def rgb_color(self) -> str:
        """Generate a color formatted as a comma-separated RGB value."""
        return ",".join(map(str, (self.random_int(0, 255) for _ in range(3))))

    def rgb_css_color(self) -> str:
        """Generate a color formatted as a CSS rgb() function."""
        return f"rgb({self.random_int(0, 255)},{self.random_int(0, 255)},{self.random_int(0, 255)})"

    @cached_property
    def _random_color(self):
        return RandomColor(self.generator)

    def color(
        self,
        hue: Optional[HueType] = None,
        luminosity: Optional[str] = None,
        color_format: str = "hex",
    ) -> str:
        """Generate a color in a human-friendly way.

        Under the hood, this method first creates a color represented in the HSV
        color model and then converts it to the desired ``color_format``. The
        argument ``hue`` controls the H value according to the following
        rules:

        - If the value is a number from ``0`` to ``360``, it will serve as the H
          value of the generated color.
        - If the value is a tuple/list of 2 numbers from 0 to 360, the color's H
          value will be randomly selected from that range.
        - If the value is a valid string, the color's H value will be randomly
          selected from the H range corresponding to the supplied string. Valid
          values are ``'monochrome'``, ``'red'``, ``'orange'``, ``'yellow'``,
          ``'green'``, ``'blue'``, ``'purple'``, and ``'pink'``.

        The argument ``luminosity`` influences both S and V values and is
        partially affected by ``hue`` as well. The finer details of this
        relationship are somewhat involved, so please refer to the source code
        instead if you wish to dig deeper. To keep the interface simple, this
        argument either can be omitted or can accept the following string
        values:``'bright'``, ``'dark'``, ``'light'``, or ``'random'``.

        The argument ``color_format`` controls in which color model the color is
        represented. Valid values are ``'hsv'``, ``'hsl'``, ``'rgb'``, or
        ``'hex'`` (default).

        :sample: hue='red'
        :sample: luminosity='light'
        :sample: hue=(100, 200), color_format='rgb'
        :sample: hue='orange', luminosity='bright'
        :sample: hue=135, luminosity='dark', color_format='hsv'
        :sample: hue=(300, 20), luminosity='random', color_format='hsl'
        """
        return self._random_color.generate(
            hue=hue,
            luminosity=luminosity,
            color_format=color_format,
        )

    def color_rgb(
        self,
        hue: Optional[HueType] = None,
        luminosity: Optional[str] = None,
    ) -> Tuple[int, int, int]:
        """Generate a RGB color tuple of integers in a human-friendly way."""
        return self._random_color.generate_rgb(hue=hue, luminosity=luminosity)

    def color_rgb_float(
        self,
        hue: Optional[HueType] = None,
        luminosity: Optional[str] = None,
    ) -> Tuple[float, float, float]:
        """Generate a RGB color tuple of floats in a human-friendly way."""
        return self._random_color.generate_rgb_float(hue=hue, luminosity=luminosity)

    def color_hsl(
        self,
        hue: Optional[HueType] = None,
        luminosity: Optional[str] = None,
    ) -> Tuple[int, int, int]:
        """Generate a HSL color tuple in a human-friendly way."""
        return self._random_color.generate_hsl(hue=hue, luminosity=luminosity)

    def color_hsv(
        self,
        hue: Optional[HueType] = None,
        luminosity: Optional[str] = None,
    ) -> Tuple[int, int, int]:
        """Generate a HSV color tuple in a human-friendly way."""
        return self._random_color.generate_hsv(hue=hue, luminosity=luminosity)
