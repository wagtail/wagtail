from decimal import Decimal
from typing import Any, Tuple

from .. import Provider as GeoProvider


class Provider(GeoProvider):
    poly = (
        ("40.34026", "19.15120"),
        ("42.21670", "26.13934"),
        ("35.55680", "29.38280"),
        ("34.15370", "22.58810"),
    )

    def local_latlng(self, *args: Any, **kwargs: Any) -> Tuple[str, str]:
        return str(self.local_latitude()), str(self.local_longitude())

    def local_latitude(self) -> Decimal:
        latitudes = [int(Decimal(t[0]) * 10000000) for t in self.poly]
        return Decimal(str(self.generator.random.randint(min(latitudes), max(latitudes)) / 10000000)).quantize(
            Decimal(".000001")
        )

    def local_longitude(self) -> Decimal:
        longitudes = [int(Decimal(t[1]) * 10000000) for t in self.poly]
        return Decimal(str(self.generator.random.randint(min(longitudes), max(longitudes)) / 10000000)).quantize(
            Decimal(".000001")
        )
