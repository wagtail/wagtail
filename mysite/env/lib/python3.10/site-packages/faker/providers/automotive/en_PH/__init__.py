from string import ascii_uppercase
from typing import List

from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    """Implement automotive provider for ``en_PH`` locale.

    Vehicle registration in the Philippines has many controversies and is full
    of quirks. On top of that, some terms are highly subject to interpretation
    or to varying definitions when applied colloquially, e.g. "motor" usually
    refers to either a machine's motor or a motorcycle, "vehicles" usually means
    cars, SUVs, vans, and trucks but not motorcycles. Please read any additional
    notes of individual methods for more details.

    Sources:

    - https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_the_Philippines
    """

    protocol_licenses = [str(x) for x in range(1, 18) if x != 15]
    motorcycle_license_formats = [
        "??####",  # 1981 series
        "??#####",  # 2014 series
    ]
    automobile_license_formats = [
        "???###",  # 1981 series
        "???####",  # 2014 series
    ]
    license_formats = motorcycle_license_formats + automobile_license_formats

    def _license_plate(self, license_format: List[str]) -> str:
        return self.bothify(self.random_element(license_format), ascii_uppercase)

    def protocol_license_plate(self) -> str:
        """Generate a protocol license plate.

        .. note::
           High ranking government officials are entitled to use low numbered
           protocol license plates.
        """
        return self.random_element(self.protocol_licenses)

    def motorcycle_license_plate(self) -> str:
        """Generate a motorcycle license plate.

        .. note::
           Motorcycles and any improvised vehicle with a motorcycle as its base
           are issued motorcycle license plates.
        """
        return self._license_plate(self.motorcycle_license_formats)

    def automobile_license_plate(self) -> str:
        """Generate an automobile license plate.

        .. note::
           Cars, SUVs, vans, trucks, and other 4-wheeled civilian vehicles are
           considered automobiles for this purpose.
        """
        return self._license_plate(self.automobile_license_formats)

    def license_plate(self) -> str:
        """Generate a license plate.

        .. note::
           This method will never generate protocol plates, because such plates
           are only for specific use cases.
        """
        return self._license_plate(self.license_formats)
