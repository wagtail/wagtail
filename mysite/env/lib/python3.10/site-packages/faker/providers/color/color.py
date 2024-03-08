"""Internal module for human-friendly color generation.

.. important::
   End users of this library should not use anything in this module.

Code adapted from:
- https://github.com/davidmerfield/randomColor  (CC0)
- https://github.com/kevinwuhoo/randomcolor-py  (MIT License)

Additional reference from:
- https://en.wikipedia.org/wiki/HSL_and_HSV
"""

import colorsys
import math
import random
import sys

from typing import TYPE_CHECKING, Dict, Hashable, Literal, Optional, Sequence, Tuple

if TYPE_CHECKING:
    from ...factory import Generator

from ...typing import HueType

ColorFormat = Literal["hex", "hsl", "hsv", "rgb"]


COLOR_MAP: Dict[str, Dict[str, Sequence[Tuple[int, int]]]] = {
    "monochrome": {
        "hue_range": [(0, 0)],
        "lower_bounds": [
            (0, 0),
            (100, 0),
        ],
    },
    "red": {
        "hue_range": [(-26, 18)],
        "lower_bounds": [
            (20, 100),
            (30, 92),
            (40, 89),
            (50, 85),
            (60, 78),
            (70, 70),
            (80, 60),
            (90, 55),
            (100, 50),
        ],
    },
    "orange": {
        "hue_range": [(19, 46)],
        "lower_bounds": [
            (20, 100),
            (30, 93),
            (40, 88),
            (50, 86),
            (60, 85),
            (70, 70),
            (100, 70),
        ],
    },
    "yellow": {
        "hue_range": [(47, 62)],
        "lower_bounds": [
            (25, 100),
            (40, 94),
            (50, 89),
            (60, 86),
            (70, 84),
            (80, 82),
            (90, 80),
            (100, 75),
        ],
    },
    "green": {
        "hue_range": [(63, 178)],
        "lower_bounds": [
            (30, 100),
            (40, 90),
            (50, 85),
            (60, 81),
            (70, 74),
            (80, 64),
            (90, 50),
            (100, 40),
        ],
    },
    "blue": {
        "hue_range": [(179, 257)],
        "lower_bounds": [
            (20, 100),
            (30, 86),
            (40, 80),
            (50, 74),
            (60, 60),
            (70, 52),
            (80, 44),
            (90, 39),
            (100, 35),
        ],
    },
    "purple": {
        "hue_range": [(258, 282)],
        "lower_bounds": [
            (20, 100),
            (30, 87),
            (40, 79),
            (50, 70),
            (60, 65),
            (70, 59),
            (80, 52),
            (90, 45),
            (100, 42),
        ],
    },
    "pink": {
        "hue_range": [(283, 334)],
        "lower_bounds": [
            (20, 100),
            (30, 90),
            (40, 86),
            (60, 84),
            (80, 80),
            (90, 75),
            (100, 73),
        ],
    },
}


class RandomColor:
    """Implement random color generation in a human-friendly way.

    This helper class encapsulates the internal implementation and logic of the
    :meth:`color() <faker.providers.color.Provider.color>` method.
    """

    def __init__(self, generator: Optional["Generator"] = None, seed: Optional[Hashable] = None) -> None:
        self.colormap = COLOR_MAP

        # Option to specify a seed was not removed so this class
        # can still be tested independently w/o generators
        if generator:
            self.random = generator.random
        else:
            self.seed = seed if seed else random.randint(0, sys.maxsize)
            self.random = random.Random(self.seed)

    def generate(
        self,
        hue: Optional[HueType] = None,
        luminosity: Optional[str] = None,
        color_format: ColorFormat = "hex",
    ) -> str:
        """Generate and format a color.

        Whenever :meth:`color() <faker.providers.color.Provider.color>` is
        called, the arguments used are simply passed into this method, and this
        method handles the rest.
        """
        # Generate HSV color tuple from picked hue and luminosity
        hsv = self.generate_hsv(hue=hue, luminosity=luminosity)

        # Return the HSB/V color in the desired string format
        return self.set_format(hsv, color_format)

    def generate_hsv(
        self,
        hue: Optional[HueType] = None,
        luminosity: Optional[str] = None,
    ) -> Tuple[int, int, int]:
        """Generate a HSV color tuple."""
        # First we pick a hue (H)
        h = self.pick_hue(hue)

        # Then use H to determine saturation (S)
        s = self.pick_saturation(h, hue, luminosity)

        # Then use S and H to determine brightness/value (B/V).
        v = self.pick_brightness(h, s, luminosity)

        return h, s, v

    def generate_rgb(
        self,
        hue: Optional[HueType] = None,
        luminosity: Optional[str] = None,
    ) -> Tuple[int, int, int]:
        """Generate a RGB color tuple of integers."""
        return self.hsv_to_rgb(self.generate_hsv(hue=hue, luminosity=luminosity))

    def generate_rgb_float(
        self,
        hue: Optional[HueType] = None,
        luminosity: Optional[str] = None,
    ) -> Tuple[float, float, float]:
        """Generate a RGB color tuple of floats."""
        return self.hsv_to_rgb_float(self.generate_hsv(hue=hue, luminosity=luminosity))

    def generate_hsl(
        self,
        hue: Optional[HueType] = None,
        luminosity: Optional[str] = None,
    ) -> Tuple[int, int, int]:
        """Generate a HSL color tuple."""
        return self.hsv_to_hsl(self.generate_hsv(hue=hue, luminosity=luminosity))

    def pick_hue(self, hue: Optional[HueType]) -> int:
        """Return a numerical hue value."""
        hue_ = self.random_within(self.get_hue_range(hue))

        # Instead of storing red as two separate ranges,
        # we group them, using negative numbers
        if hue_ < 0:
            hue_ += 360

        return hue_

    def pick_saturation(self, hue: int, hue_name: Optional[HueType], luminosity: Optional[str]) -> int:
        """Return a numerical saturation value."""
        if luminosity is None:
            luminosity = ""
        if luminosity == "random":
            return self.random_within((0, 100))

        if isinstance(hue_name, str) and hue_name == "monochrome":
            return 0

        s_min, s_max = self.get_saturation_range(hue)

        if luminosity == "bright":
            s_min = 55
        elif luminosity == "dark":
            s_min = s_max - 10
        elif luminosity == "light":
            s_max = 55

        return self.random_within((s_min, s_max))

    def pick_brightness(self, h: int, s: int, luminosity: Optional[str]) -> int:
        """Return a numerical brightness value."""
        if luminosity is None:
            luminosity = ""

        b_min = self.get_minimum_brightness(h, s)
        b_max = 100

        if luminosity == "dark":
            b_max = b_min + 20
        elif luminosity == "light":
            b_min = (b_max + b_min) // 2
        elif luminosity == "random":
            b_min = 0
            b_max = 100

        return self.random_within((b_min, b_max))

    def set_format(self, hsv: Tuple[int, int, int], color_format: ColorFormat) -> str:
        """Handle conversion of HSV values into desired format."""
        if color_format == "hsv":
            color = f"hsv({hsv[0]}, {hsv[1]}, {hsv[2]})"

        elif color_format == "hsl":
            hsl = self.hsv_to_hsl(hsv)
            color = f"hsl({hsl[0]}, {hsl[1]}, {hsl[2]})"

        elif color_format == "rgb":
            rgb = self.hsv_to_rgb(hsv)
            color = f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})"

        else:
            rgb = self.hsv_to_rgb(hsv)
            color = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

        return color

    def get_minimum_brightness(self, h: int, s: int) -> int:
        """Return the minimum allowed brightness for ``h`` and ``s``."""
        lower_bounds: Sequence[Tuple[int, int]] = self.get_color_info(h)["lower_bounds"]

        for i in range(len(lower_bounds) - 1):
            s1, v1 = lower_bounds[i]
            s2, v2 = lower_bounds[i + 1]

            if s1 <= s <= s2:
                m: float = (v2 - v1) / (s2 - s1)
                b: float = v1 - m * s1

                return int(m * s + b)

        return 0

    def _validate_color_input(self, color_input: HueType) -> Tuple[int, int]:
        if (
            not isinstance(color_input, (list, tuple))
            or len(color_input) != 2
            or any(not isinstance(c, (float, int)) for c in color_input)
        ):
            raise TypeError("Hue must be a valid string, numeric type, or a tuple/list of 2 numeric types.")

        return color_input[0], color_input[1]

    def get_hue_range(self, color_input: Optional[HueType]) -> Tuple[int, int]:
        """Return the hue range for a given ``color_input``."""
        if color_input is None:
            return 0, 360

        if isinstance(color_input, (int, float)) and 0 <= color_input <= 360:
            color_input = int(color_input)
            return color_input, color_input

        if isinstance(color_input, str) and color_input in self.colormap:
            return self.colormap[color_input]["hue_range"][0]

        color_input = self._validate_color_input(color_input)

        v1 = int(color_input[0])
        v2 = int(color_input[1])

        if v2 < v1:
            v1, v2 = v2, v1
        v1 = max(v1, 0)
        v2 = min(v2, 360)
        return v1, v2

    def get_saturation_range(self, hue: int) -> Tuple[int, int]:
        """Return the saturation range for a given numerical ``hue`` value."""
        saturation_bounds = [s for s, v in self.get_color_info(hue)["lower_bounds"]]
        return min(saturation_bounds), max(saturation_bounds)

    def get_color_info(self, hue: int) -> Dict[str, Sequence[Tuple[int, int]]]:
        """Return the color info for a given numerical ``hue`` value."""
        # Maps red colors to make picking hue easier
        if 334 <= hue <= 360:
            hue -= 360

        for color_name, color in self.colormap.items():
            hue_range: Tuple[int, int] = color["hue_range"][0]
            if hue_range[0] <= hue <= hue_range[1]:
                return self.colormap[color_name]
        else:
            raise ValueError("Value of hue `%s` is invalid." % hue)

    def random_within(self, r: Sequence[int]) -> int:
        """Return a random integer within the range ``r``."""
        return self.random.randint(int(r[0]), int(r[1]))

    @classmethod
    def hsv_to_rgb_float(cls, hsv: Tuple[int, int, int]) -> Tuple[float, float, float]:
        """Convert HSV to RGB.

        This method expects ``hsv`` to be a 3-tuple of H, S, and V values, and
        it will return a 3-tuple of the equivalent R, G, and B float values.
        """
        h, s, v = hsv
        h = max(h, 1)
        h = min(h, 359)

        return colorsys.hsv_to_rgb(h / 360, s / 100, v / 100)

    @classmethod
    def hsv_to_rgb(cls, hsv: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """Convert HSV to RGB.

        This method expects ``hsv`` to be a 3-tuple of H, S, and V values, and
        it will return a 3-tuple of the equivalent R, G, and B integer values.
        """
        r, g, b = cls.hsv_to_rgb_float(hsv)
        return int(r * 255), int(g * 255), int(b * 255)

    @classmethod
    def hsv_to_hsl(cls, hsv: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """Convert HSV to HSL.

        This method expects ``hsv`` to be a 3-tuple of H, S, and V values, and
        it will return a 3-tuple of the equivalent H, S, and L values.
        """
        h, s, v = hsv

        s_: float = s / 100.0
        v_: float = v / 100.0
        l = 0.5 * v_ * (2 - s_)  # noqa: E741

        s_ = 0.0 if l in [0, 1] else v_ * s_ / (1 - math.fabs(2 * l - 1))
        return int(h), int(s_ * 100), int(l * 100)
