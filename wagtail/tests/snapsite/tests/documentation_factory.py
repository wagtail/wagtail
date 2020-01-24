import os

from django.conf import settings
from PIL import Image, ImageDraw


def dashed_line(draw, x1, y1, x2, y2, line=9, gap=9, color="#ff00ea", stroke_width=4):
    if x1 == x2:  # Vertical line
        x = x1
        for y in range(y1, y2, line + gap):
            draw.line([x, y, x, min(y + line, y2)], fill=color, width=stroke_width)

    if y1 == y2:  # Horizontal line
        y = y1
        for x in range(x1, x2, line + gap):
            draw.line([x, y, min(x + line, x2), y], fill=color, width=stroke_width)


def rectangle(draw, x, y, width, height, scale_factor=1):
    x *= scale_factor
    y *= scale_factor
    width *= scale_factor
    height *= scale_factor
    stroke = 4 * scale_factor

    # Adjust the box so it is on the outside of the element.
    x -= stroke
    y -= stroke
    width += 2 * stroke
    height += 2 * stroke
    dashed_line(draw, x, y, x + width, y)  # top
    dashed_line(draw, x + width, y, x + width, y + height)  # right
    dashed_line(draw, x, y + height, x + width, y + height)  # bottom
    dashed_line(draw, x, y, x, y + height)  # left


def nested_list(items, prefix=""):
    content = ""
    for item in items:
        if isinstance(item, list):
            content += "\n"
            content += nested_list(item, prefix="  ")
        else:
            content += f"{prefix}- {item}\n"
    return content


class DocumentationFactory:
    def __init__(self, filename, title, driver, scale_factor=1):
        self.blocks = []
        self.docs_dir = os.path.join(settings.BASE_DIR, "..", "..",  "..", "docs")
        self.filename = os.path.join(self.docs_dir, filename)
        self.h1(title)
        self.driver = driver
        self.scale_factor = scale_factor

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        # with open(self.filename, "w") as doc:
        #     doc.write("\n\n".join(self.blocks))
        pass

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

    def img(self, filename, element=None, directory=None):
        if not directory:
            directory = os.path.join(self.docs_dir, "_static", "images")
        if not os.path.exists(directory):
            os.mkdir(directory)
        filepath = os.path.join(directory, filename)
        self.driver.save_screenshot(filepath)
        self.blocks.append(f".. image:: /_static/images/{filename}")
        if element:
            im = Image.open(filepath)
            draw = ImageDraw.Draw(im)
            pos_x = element.location["x"]

            # Compensate y position for the window y offset.
            offset_y = int(self.driver.execute_script("return window.pageYOffset;"))
            pos_y = element.location["y"] - offset_y

            width = element.size["width"]
            height = element.size["height"]
            rectangle(draw, pos_x, pos_y, width, height, scale_factor=self.scale_factor)
            im.save(filepath, format="PNG")
