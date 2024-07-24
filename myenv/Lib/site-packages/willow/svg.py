import re
from collections import namedtuple
from copy import copy
from xml.etree.ElementTree import ElementTree

from .image import BadImageOperationError, Image, SvgImageFile


class WillowSvgException(Exception):
    pass


class InvalidSvgAttribute(WillowSvgException):
    pass


class InvalidSvgSizeAttribute(WillowSvgException):
    pass


class SvgViewBoxParseError(WillowSvgException):
    pass


ViewBox = namedtuple("ViewBox", "min_x min_y width height")


def view_box_to_attr_str(view_box):
    return f"{view_box.min_x} {view_box.min_y} {view_box.width} {view_box.height}"


class ViewportToUserSpaceTransform:
    def __init__(self, scale_x, scale_y, translate_x, translate_y):
        self.scale_x = scale_x
        self.scale_y = scale_y
        self.translate_x = translate_x
        self.translate_y = translate_y

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(scale_x={self.scale_x}, scale_y="
            f"{self.scale_y}, translate_x={self.translate_x}, "
            f"translate_y={self.translate_y})"
        )

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return (
            self.scale_x == other.scale_x
            and self.scale_y == other.scale_y
            and self.translate_x == other.translate_x
            and self.translate_y == other.translate_y
        )

    def __call__(self, rect):
        left, top, right, bottom = rect
        return (
            (left + self.translate_x) / self.scale_x,
            (top + self.translate_y) / self.scale_y,
            (right + self.translate_x) / self.scale_x,
            (bottom + self.translate_y) / self.scale_y,
        )


def get_viewport_to_user_space_transform(
    svg: "SvgImage",
) -> ViewportToUserSpaceTransform:
    # cairosvg used as a reference
    view_box = svg.image.view_box

    preserve_aspect_ratio = svg.image.preserve_aspect_ratio.split()
    try:
        align, meet_or_slice = preserve_aspect_ratio
    except ValueError:
        align = preserve_aspect_ratio[0]
        meet_or_slice = None

    scale_x = svg.image.width / view_box.width
    scale_y = svg.image.height / view_box.height

    if align == "none":
        # if align is "none", the viewBox will be scaled non-uniformly,
        # so we keep and use both scale_x and scale_y
        x_position = "min"
        y_position = "min"
    else:
        x_position = align[1:4].lower()
        y_position = align[5:].lower()
        choose_coefficient = max if meet_or_slice == "slice" else min
        # all values of preserveAspectRatio's `align', other than
        # "none", force uniform scaling, so choose the appropriate
        # coefficient and use it for scaling both axes
        scale_x = scale_y = choose_coefficient(scale_x, scale_y)

    # initial offsets to account for non-zero viewBox min-x and min-y
    translate_x = view_box.min_x * scale_x
    translate_y = view_box.min_y * scale_y

    # adjust the offsets by the amount the viewBox has been translated
    # to fit into the viewport (if any)
    if x_position == "mid":
        translate_x -= (svg.image.width - view_box.width * scale_x) / 2
    elif x_position == "max":
        translate_x -= svg.image.width - view_box.width * scale_x

    if y_position == "mid":
        translate_y -= (svg.image.height - view_box.height * scale_y) / 2
    elif y_position == "max":
        translate_y -= svg.image.height - view_box.height * scale_y

    return ViewportToUserSpaceTransform(scale_x, scale_y, translate_x, translate_y)


class SvgWrapper:
    # https://developer.mozilla.org/en-US/docs/Web/SVG/Content_type#length
    UNIT_RE = re.compile(r"(?:em|ex|px|in|cm|mm|pt|pc|%)$")

    # https://www.w3.org/TR/SVG11/types.html#DataTypeNumber
    # https://www.w3.org/TR/2013/WD-SVG2-20130409/types.html#DataTypeNumber
    # This will exclude some inputs that Python will accept (e.g. "1.e9", "1."),
    # but for integration with other tools, we should adhere to the spec
    NUMBER_PATTERN = r"([+-]?(?:\d*\.)?\d+(?:[Ee][+-]?\d+)?)"

    # https://www.w3.org/Graphics/SVG/1.1/coords.html#ViewBoxAttribute
    VIEW_BOX_RE = re.compile(
        rf"^{NUMBER_PATTERN}(?:,\s*|\s+){NUMBER_PATTERN}(?:,\s*|\s+)"
        rf"{NUMBER_PATTERN}(?:,\s*|\s+){NUMBER_PATTERN}$"
    )

    PRESERVE_ASPECT_RATIO_RE = re.compile(
        r"^none$|^x(Min|Mid|Max)Y(Min|Mid|Max)(\s+(meet|slice))?$",
    )

    # Borrowed from cairosvg
    COEFFICIENTS = {
        "mm": 1 / 25.4,
        "cm": 1 / 2.54,
        "in": 1,
        "pt": 1 / 72.0,
        "pc": 1 / 6.0,
    }

    def __init__(self, dom: ElementTree, dpi=96, font_size_px=16):
        self.dom = dom
        self.dpi = dpi
        self.font_size_px = font_size_px
        self.view_box = self._get_view_box()
        self.preserve_aspect_ratio = self._get_preserve_aspect_ratio()

        width, width_unit = self._get_width()
        height, height_unit = self._get_height()
        # If one attr is missing or relative, we fall back to the other. After
        # this either both will be valid, or neither will, which will be handled
        # below. Relative width/height are treated as being undefined - so fall
        # back first to the other attribute, then the viewBox, then the browser
        # fallback. This gives us some flexibility for real world use cases, where
        # SVGs may have a relative height, a relative width, or both
        if width is None:
            width = height
            width_unit = height_unit
        elif height is None:
            height = width
            height_unit = width_unit
        elif width_unit == "%":
            width = height
            width_unit = height_unit
        elif height_unit == "%":
            height = width
            height_unit = width_unit

        # If the root svg element has no width, height, or viewBox attributes,
        # emulate browser behaviour and set width and height to 300 and 150
        # respectively, and set the viewBox to match
        # (https://svgwg.org/specs/integration/#svg-css-sizing). This means we
        # can always crop and resize without needing to rasterise
        if width is None and height is None or width_unit == "%" and height_unit == "%":
            if self.view_box is not None:
                self.width = self.view_box.width
                self.height = self.view_box.height
            else:
                self.width = 300
                self.height = 150
        else:
            self.width = self._convert_to_px(width, width_unit)
            self.height = self._convert_to_px(height, height_unit)
        if self.view_box is None:
            self.view_box = ViewBox(0, 0, self.width, self.height)

    def __copy__(self):
        # copy() called on ElementTree.Element makes a shallow copy (child
        # elements are shared with the original) so is efficient enough - we
        # only need to copy the root SVG element, as that is the only element
        # we will mutate
        dom = ElementTree(copy(self.dom.getroot()))
        return self.__class__(dom, dpi=self.dpi, font_size_px=self.font_size_px)

    @classmethod
    def from_file(cls, f):
        return cls(SvgImageFile(f).dom)

    @property
    def root(self):
        return self.dom.getroot()

    def _get_preserve_aspect_ratio(self):
        value = self.root.get("preserveAspectRatio", "").strip()
        if value == "":
            return "xMidYMid meet"
        if not self.PRESERVE_ASPECT_RATIO_RE.match(value):
            raise InvalidSvgAttribute(
                f"Unable to parse preserveAspectRatio value '{value}'"
            )
        return value

    def _get_width(self):
        attr_value = self.root.get("width")
        if attr_value:
            return self._parse_size(attr_value)
        return None, None

    def _get_height(self):
        attr_value = self.root.get("height")
        if attr_value:
            return self._parse_size(attr_value)
        return None, None

    def _parse_size(self, raw_value):
        clean_value = raw_value.strip()
        match = self.UNIT_RE.search(clean_value)
        unit = clean_value[match.start() :] if match else None
        amount_raw = clean_value[: -len(unit)] if unit else clean_value
        try:
            amount = float(amount_raw)
        except ValueError as err:
            raise InvalidSvgSizeAttribute(
                f"Unable to parse value from '{raw_value}'"
            ) from err
        if amount <= 0:
            raise InvalidSvgSizeAttribute(f"Negative or 0 sizes are invalid ({amount})")
        return amount, unit

    def _convert_to_px(self, size, unit):
        if unit in (None, "px"):
            return size
        elif unit == "em":
            return size * self.font_size_px
        elif unit == "ex":
            # This is not exactly correct, but it's the best we can do
            return size * self.font_size_px / 2
        else:
            return size * self.dpi * self.COEFFICIENTS[unit]

    def _get_view_box(self):
        attr_value = self.root.get("viewBox")
        if attr_value:
            return self._parse_view_box(attr_value)

    @classmethod
    def _parse_view_box(cls, raw_value):
        match = cls.VIEW_BOX_RE.match(raw_value.strip())
        if match is None:
            raise SvgViewBoxParseError(f"Unable to parse viewBox value '{raw_value}'")
        return ViewBox(*map(float, match.groups()))

    def set_root_attr(self, attr, value):
        self.root.set(attr, str(value))

    def set_width(self, width):
        self.set_root_attr("width", width)
        self.width = width

    def set_height(self, height):
        self.set_root_attr("height", height)
        self.height = height

    def set_view_box(self, view_box):
        self.set_root_attr("viewBox", view_box_to_attr_str(view_box))
        self.view_box = view_box

    def write(self, f):
        self.dom.write(f, encoding="utf-8")


class SvgImage(Image):
    def __init__(self, image):
        self.image: SvgWrapper = image

    @Image.operation
    def crop(self, rect, get_transformer=get_viewport_to_user_space_transform):
        left, top, right, bottom = rect
        if left >= right or top >= bottom:
            raise BadImageOperationError(f"Invalid crop dimensions: {rect}")

        viewport_width = right - left
        viewport_height = bottom - top

        transformed_rect = get_transformer(self)(rect)
        left, top, right, bottom = transformed_rect

        svg_wrapper = copy(self.image)
        view_box_width = right - left
        view_box_height = bottom - top
        svg_wrapper.set_view_box(ViewBox(left, top, view_box_width, view_box_height))
        svg_wrapper.set_width(viewport_width)
        svg_wrapper.set_height(viewport_height)
        return self.__class__(image=svg_wrapper)

    @Image.operation
    def resize(self, size):
        new_width, new_height = size
        if new_width < 1 or new_height < 1:
            raise BadImageOperationError(f"Invalid resize dimensions: {size}")

        svg_wrapper = copy(self.image)
        svg_wrapper.set_width(new_width)
        svg_wrapper.set_height(new_height)
        return self.__class__(image=svg_wrapper)

    @Image.operation
    def get_size(self):
        return (self.image.width, self.image.height)

    @Image.operation
    def auto_orient(self):
        return self

    @Image.operation
    def has_animation(self):
        return False

    @Image.operation
    def get_frame_count(self):
        return 1

    def write(self, f):
        self.image.write(f)
        f.seek(0)

    @Image.operation
    def save_as_svg(self, f):
        self.write(f)
        return SvgImageFile(f, dom=self.image.dom)

    @classmethod
    @Image.converter_from(SvgImageFile)
    def open(cls, svg_image_file):
        return cls(image=SvgWrapper(svg_image_file.dom))
