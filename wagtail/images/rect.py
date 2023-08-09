import math


class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __iter__(self):
        return iter((self.x, self.y))

    def __getitem__(self, key):
        return (self.x, self.y)[key]

    def __eq__(self, other):
        return tuple(self) == tuple(other)

    def __repr__(self):
        return "Vector(x: %d, y: %d)" % (self.x, self.y)


class Rect:
    def __init__(self, left, top, right, bottom):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom

    def _get_size(self):
        return Vector(self.right - self.left, self.bottom - self.top)

    def _set_size(self, new_size):
        centroid = self.centroid
        self.left = centroid[0] - new_size[0] / 2
        self.right = centroid[0] + new_size[0] / 2
        self.top = centroid[1] - new_size[1] / 2
        self.bottom = centroid[1] + new_size[1] / 2

    size = property(_get_size, _set_size)

    @property
    def width(self):
        return self.size.x

    @property
    def height(self):
        return self.size.y

    def _get_centroid(self):
        return Vector((self.left + self.right) / 2, (self.top + self.bottom) / 2)

    def _set_centroid(self, new_centroid):
        size = self.size
        self.left = new_centroid[0] - size[0] / 2
        self.right = new_centroid[0] + size[0] / 2
        self.top = new_centroid[1] - size[1] / 2
        self.bottom = new_centroid[1] + size[1] / 2

    centroid = property(_get_centroid, _set_centroid)

    @property
    def x(self):
        return self.centroid.x

    @property
    def y(self):
        return self.centroid.y

    @property
    def centroid_x(self):
        # Included for backwards compatibility
        return self.centroid.x

    @property
    def centroid_y(self):
        # Included for backwards compatibility
        return self.centroid.y

    def as_tuple(self):
        # No longer needed, this class should behave like a tuple
        # Included for backwards compatibility
        return self.left, self.top, self.right, self.bottom

    def clone(self):
        return type(self)(self.left, self.top, self.right, self.bottom)

    def round(self):
        """
        Returns a new rect with all attributes rounded to integers
        """
        clone = self.clone()

        # Round down left and top
        clone.left = int(math.floor(clone.left))
        clone.top = int(math.floor(clone.top))

        # Round up right and bottom
        clone.right = int(math.ceil(clone.right))
        clone.bottom = int(math.ceil(clone.bottom))

        return clone

    def move_to_clamp(self, other):
        """
        Moves this rect so it is completely covered by the rect in "other" and
        returns a new Rect instance.
        """
        other = Rect(*other)
        clone = self.clone()

        if clone.left < other.left:
            clone.right -= clone.left - other.left
            clone.left = other.left

        if clone.top < other.top:
            clone.bottom -= clone.top - other.top
            clone.top = other.top

        if clone.right > other.right:
            clone.left -= clone.right - other.right
            clone.right = other.right

        if clone.bottom > other.bottom:
            clone.top -= clone.bottom - other.bottom
            clone.bottom = other.bottom

        return clone

    def move_to_cover(self, other):
        """
        Moves this rect so it completely covers the rect specified in the
        "other" parameter and returns a new Rect instance.
        """
        other = Rect(*other)
        clone = self.clone()

        if clone.left > other.left:
            clone.right -= clone.left - other.left
            clone.left = other.left

        if clone.top > other.top:
            clone.bottom -= clone.top - other.top
            clone.top = other.top

        if clone.right < other.right:
            clone.left += other.right - clone.right
            clone.right = other.right

        if clone.bottom < other.bottom:
            clone.top += other.bottom - clone.bottom
            clone.bottom = other.bottom

        return clone

    def transform(self, transform):
        # Transform each corner of the rect
        tl_transformed = transform.transform_vector(Vector(self.left, self.top))
        tr_transformed = transform.transform_vector(Vector(self.right, self.top))
        bl_transformed = transform.transform_vector(Vector(self.left, self.bottom))
        br_transformed = transform.transform_vector(Vector(self.right, self.bottom))

        # Find extents of the transformed corners
        left = min(
            [tl_transformed.x, tr_transformed.x, bl_transformed.x, br_transformed.x]
        )
        right = max(
            [tl_transformed.x, tr_transformed.x, bl_transformed.x, br_transformed.x]
        )
        top = min(
            [tl_transformed.y, tr_transformed.y, bl_transformed.y, br_transformed.y]
        )
        bottom = max(
            [tl_transformed.y, tr_transformed.y, bl_transformed.y, br_transformed.y]
        )

        return Rect(left, top, right, bottom)

    def __iter__(self):
        return iter((self.left, self.top, self.right, self.bottom))

    def __getitem__(self, key):
        return (self.left, self.top, self.right, self.bottom)[key]

    def __eq__(self, other):
        return tuple(self) == tuple(other)

    def __repr__(self):
        return "Rect(left: %d, top: %d, right: %d, bottom: %d)" % (
            self.left,
            self.top,
            self.right,
            self.bottom,
        )

    @classmethod
    def from_point(cls, x, y, width, height):
        return cls(
            x - width / 2,
            y - height / 2,
            x + width / 2,
            y + height / 2,
        )
