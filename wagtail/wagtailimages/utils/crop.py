class CropBox(object):
    def __init__(self, left, top, right, bottom):
        self.left = int(left)
        self.top = int(top)
        self.right = int(right)
        self.bottom = int(bottom)

    def __getitem__(self, key):
        return (self.left, self.top, self.right, self.bottom)[key]

    @property
    def width(self):
        return self.right - self.left

    @property
    def height(self):
        return self.bottom - self.top

    @property
    def size(self):
        return self.width, self.height


def crop_to_centre(image_size, crop_size):
    (original_width, original_height) = image_size
    (crop_width, crop_height) = crop_size

    # final dimensions should not exceed original dimensions
    final_width = min(original_width, crop_width)
    final_height = min(original_height, crop_height)

    left = (original_width - final_width) / 2
    top = (original_height - final_height) / 2

    return CropBox(left, top, left + final_width, top + final_height)
