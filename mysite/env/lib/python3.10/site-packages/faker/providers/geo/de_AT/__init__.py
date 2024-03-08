from decimal import Decimal

from .. import Provider as GeoProvider


class Provider(GeoProvider):
    def local_latitude(self) -> Decimal:
        return self.coordinate(center=47.60707, radius=1)

    def local_longitude(self) -> Decimal:
        return self.coordinate(center=13.37208, radius=2)
