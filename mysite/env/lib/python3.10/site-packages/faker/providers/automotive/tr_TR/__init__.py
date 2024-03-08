import re

from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    """Implement automotive provider for ``tr_TR`` locale.

    Sources:

    - https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_Turkey
    """

    license_formats = (
        "## ? ####",
        "## ? #####",
        "## ?? ###",
        "## ?? ####",
        "## ??? ##",
        "## ??? ###",
    )
    ascii_uppercase_turkish = "ABCDEFGHIJKLMNOPRSTUVYZ"

    def license_plate(self) -> str:
        """Generate a license plate."""
        temp = re.sub(
            r"\?",
            lambda x: self.random_element(self.ascii_uppercase_turkish),
            self.random_element(self.license_formats),
        )
        temp = temp.replace("##", "{:02d}", 1)
        temp = temp.format(self.random_element(range(1, 82)))
        return self.numerify(temp)
