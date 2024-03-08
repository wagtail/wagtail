import re

from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    """Implement automotive provider for ``vi_VN`` locale.

    Sources:

    - https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_Vietnam
    """

    license_formats = ("##?-#####",)
    ascii_uppercase_vietnamese = "ABCDĐEFGHKLMNPSTUVXYZ"

    def license_plate(self) -> str:
        """Generate a license plate."""
        temp = re.sub(
            r"\?",
            lambda x: self.random_element(self.ascii_uppercase_vietnamese),
            self.random_element(self.license_formats),
        )
        return self.numerify(temp)
