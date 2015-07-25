from __future__ import division


class Vector(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __iter__(self):
        return iter((self.x, self.y))

    def __getitem__(self, key):
        return (self.x, self.y)[key]

    def __eq__(self, other):
        return tuple(self) == tuple(other)

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return 'Vector(x: %d, y: %d)' % (
            self.x, self.y
        )


class Rect(object):
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

    def __iter__(self):
        return iter((self.left, self.top, self.right, self.bottom))

    def __getitem__(self, key):
        return (self.left, self.top, self.right, self.bottom)[key]

    def __eq__(self, other):
        return tuple(self) == tuple(other)

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return 'Rect(left: %d, top: %d, right: %d, bottom: %d)' % (
            self.left, self.top, self.right, self.bottom
        )

    @classmethod
    def from_point(cls, x, y, width, height):
        return cls(
            x - width / 2,
            y - height / 2,
            x + width / 2,
            y + height / 2,
        )
