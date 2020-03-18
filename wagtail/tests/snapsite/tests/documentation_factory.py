import os

from django.conf import settings
from PIL import Image, ImageDraw


def nested_list(items, prefix=""):
    content = ""
    for item in items:
        if isinstance(item, list):
            content += "\n"
            content += nested_list(item, prefix="  ")
        else:
            content += f"{prefix}- {item}\n"
    return content


def add_browser_chrome(filepath):
    original = Image.open(filepath).convert('RGBA')
    width, height = original.size
    chrome_height = 159
    im = Image.new("RGBA", (width + 2, height + chrome_height + 1), (0, 0, 0, 89))
    im.paste(original, (1, chrome_height))
    chrome_middle = Image.open("tests/images/chrome_middle.png").convert("RGBA")
    for i in range(width):
        im.paste(chrome_middle, (i, 0))
    chrome_start = Image.open("tests/images/chrome_start.png").convert("RGBA")
    im.paste(chrome_start, (0, 0))
    chrome_end = Image.open("tests/images/chrome_end.png").convert("RGBA")
    chrome_end_width, _ = chrome_end.size
    im.paste(chrome_end, (width + 2 - chrome_end_width, 0))
    im.save(filepath, format="PNG")


class DocumentationFactory:
    stroke_color = "#ff00ea"

    def __init__(self, filename, title, driver, scale_factor=1):
        self.blocks = []
        self.docs_dir = os.path.join(settings.BASE_DIR, "..", "..",  "..", "docs")
        self.filename = os.path.join(self.docs_dir, filename)
        self.h1(title)
        self.driver = driver
        self.scale_factor = scale_factor
        self.stroke_width = 4 * scale_factor
        self.line = 9 * scale_factor
        self.gap = 9 * scale_factor

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        with open(self.filename, "w") as doc:
            doc.write("\n\n".join(self.blocks))

    def comment(self, content):
        self.blocks.append(f".. {content}")

    def h1(self, content):
        self.blocks.append(f"{content}\n" f"{len(content) * '-'}")

    def h2(self, content):
        self.blocks.append(f"{content}\n{len(content) * '_'}")

    def p(self, content):
        self.blocks.append(content)

    def ul(self, items):
        self.blocks.append(nested_list(items))

    def ol(self, items):
        self.blocks.append("\n".join([f"{idx + 1}. {item}" for idx, item in enumerate(items)]) + "\n")

    def _save_image(self, filename, directory=None):
        if not directory:
            directory = os.path.join(self.docs_dir, "_static", "images")
        if not os.path.exists(directory):
            os.mkdir(directory)
        filepath = os.path.join(directory, filename)
        self.driver.save_screenshot(filepath)
        self.blocks.append(f".. image:: /_static/images/{filename}")
        return filepath

    def _get_box(self, element):
        """Element coordinates to PIL coordinates"""
        pos_x = element.location["x"] * self.scale_factor
        offset_y = int(self.driver.execute_script("return window.pageYOffset;"))
        pos_y = element.location["y"] - offset_y
        pos_y *= self.scale_factor
        width = element.size["width"] * self.scale_factor
        height = element.size["height"] * self.scale_factor
        width += self.scale_factor
        return pos_x, pos_y, width, height

    def _get_highlight_box(self, element):
        """
        The highlight box draws around the element. Add line width.
        """
        pos_x, pos_y, width, height = self._get_box(element)
        stroke = self.stroke_width * self.scale_factor
        pos_x -= stroke
        pos_y -= stroke
        width += 2 * stroke
        height += 2 * stroke
        return pos_x, pos_y, width, height

    def img(self, filename, element=None, directory=None, browser=False):
        filepath = self._save_image(filename, directory=directory)
        if element:
            im = Image.open(filepath)
            draw = ImageDraw.Draw(im)
            pos_x, pos_y, width, height = self._get_highlight_box(element)
            self.rectangle(draw, pos_x, pos_y, width, height)
            im.save(filepath, format="PNG")
        if browser:
            add_browser_chrome(filepath)

    def crop(self, filename, element=None, directory=None, padding=None):
        filepath = self._save_image(filename, directory=directory)
        if padding:
            top, right, bottom, left = padding
        else:
            top, right, bottom, left = 0, 0, 0, 0
        if element:
            im = Image.open(filepath)
            pos_x, pos_y, width, height = self._get_box(element)
            im = im.crop((pos_x - left, pos_y - top, pos_x + width + left + right, pos_y + height + bottom))
            im.save(filepath, format="PNG")

    def dashed_line(self, draw, x1, y1, x2, y2):
        if x1 == x2:  # Vertical line
            x = x1
            for y in range(y1, y2, self.line + self.gap):
                draw.line([x, y, x, min(y + self.line, y2)], fill=self.stroke_color, width=self.stroke_width)

        if y1 == y2:  # Horizontal line
            y = y1
            for x in range(x1, x2, self.line + self.gap):
                draw.line([x, y, min(x + self.line, x2), y], fill=self.stroke_color, width=self.stroke_width)

    def rectangle(self, draw, x, y, width, height):
        self.dashed_line(draw, x, y, x + width, y)  # top
        self.dashed_line(draw, x + width, y, x + width, y + height)  # right
        self.dashed_line(draw, x, y + height, x + width, y + height)  # bottom
        self.dashed_line(draw, x, y, x, y + height)  # left