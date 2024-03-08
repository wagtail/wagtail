from collections import OrderedDict

from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    license_formats = OrderedDict(
        [
            ("???###", 0.6),
            ("???##?", 0.3),
            ("T####", 0.03),
            ("??####", 0.01),
            ("R#####", 0.03),
            ("S#####", 0.03),
        ]
    )
