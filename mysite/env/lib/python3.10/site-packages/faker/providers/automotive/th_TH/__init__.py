import re

from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    """Implement automotive provider for ``th_TH`` locale.

    Sources:

    - https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_Thailand
    """

    license_formats = (
        "# ?? ####",
        "# ?? ###",
        "# ?? ##",
        "# ?? #",
        "?? ####",
        "?? ###",
        "?? ##",
        "?? #",
        "??? ###",
        "??? ##",
        "??? #",
        "##-####",
    )

    thai_consonants = "กขฃคฅฆงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรลวศษสหฬอฮ"

    def license_plate(self) -> str:
        """Generate a license plate."""

        temp = re.sub(
            r"\?",
            lambda x: self.random_element(self.thai_consonants),
            self.random_element(self.license_formats),
        )
        return self.numerify(temp)
