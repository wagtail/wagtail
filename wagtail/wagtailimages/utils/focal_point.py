# https://github.com/thumbor/thumbor/blob/8a50bfba9443e8d2a1a691ab20eeb525815be597/thumbor/point.py

# thumbor imaging service
# https://github.com/globocom/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com


class FocalPoint(object):
    ALIGNMENT_PERCENTAGES = {
        'left': 0.0,
        'center': 0.5,
        'right': 1.0,
        'top': 0.0,
        'middle': 0.5,
        'bottom': 1.0
    }

    def to_dict(self):
        return {
            'x': self.x,
            'y': self.y,
            'z': self.weight,
            'height': self.height,
            'width': self.width,
            'origin': self.origin
        }

    @classmethod
    def from_dict(cls, values):
        return cls(
            x=float(values['x']),
            y=float(values['y']),
            weight=float(values['z']),
            width=float(values.get('width', 1)),
            height=float(values.get('height', 1)),
            origin=values.get('origin', 'alignment')
        )

    def __init__(self, x, y, height=1, width=1, weight=1.0, origin="alignment"):
        self.x = x
        self.y = y
        self.height = height
        self.width = width
        self.weight = weight
        self.origin = origin

    @classmethod
    def from_square(cls, x, y, width, height, origin='detection'):
        center_x = x + (width / 2)
        center_y = y + (height / 2)
        return cls(center_x, center_y, height=height, width=width, weight=width * height, origin=origin)

    @classmethod
    def from_alignment(cls, halign, valign, width, height):
        x = width * cls.ALIGNMENT_PERCENTAGES[halign]
        y = height * cls.ALIGNMENT_PERCENTAGES[valign]

        return cls(x, y)

    def __repr__(self):
        return 'FocalPoint(x: %d, y: %d, width: %d, height: %d, weight: %d, origin: %s)' % (
            self.x, self.y, self.width, self.height, self.weight, self.origin
        )


def combine_focal_points(focal_points):
    # https://github.com/thumbor/thumbor/blob/fc75f2d617942e3548986fe8403ad717fc9978ba/thumbor/transformer.py#L255-L269
    if not focal_points:
        return

    total_weight = 0.0
    total_x = 0.0
    total_y = 0.0

    for focal_point in focal_points:
        total_weight += focal_point.weight

        total_x += focal_point.x * focal_point.weight
        total_y += focal_point.y * focal_point.weight

    x = total_x / total_weight
    y = total_y / total_weight

    min_x = min([point.x - point.width / 2 for point in focal_points])
    min_y = min([point.y - point.height / 2 for point in focal_points])
    max_x = max([point.x + point.width / 2 for point in focal_points])
    max_y = max([point.y + point.height / 2 for point in focal_points])

    width = max_x - min_x
    height = max_y - min_y

    return FocalPoint(x, y, width=width, height=height, weight=total_weight)


def largest_point(focal_points):
    return sorted(focal_points, key=lambda point: point.weight, reverse=True)[0]
