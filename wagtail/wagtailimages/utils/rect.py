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
