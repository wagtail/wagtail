from __future__ import division


class Rect(object):
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

    @property
    def centroid_x(self):
        return (self.left + self.right) / 2

    @property
    def centroid_y(self):
        return (self.top + self.bottom) / 2

    @property
    def centroid(self):
        return self.centroid_x, self.centroid_y

    def as_tuple(self):
        return self.left, self.top, self.right, self.bottom

    def __eq__(self, other):
        return self.as_tuple() == other.as_tuple()

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


    # DELETEME
    def get_key(self):
        return "%(x)d-%(y)d-%(width)dx%(height)d" % {
            'x': int(self.centroid_x),
            'y': int(self.centroid_y),
            'width': int(self.width),
            'height': int(self.height),
        }
