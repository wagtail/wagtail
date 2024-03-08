import re

from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    """Implement automotive provider for ``el_GR`` locale."""

    uppercase_letters = "ABEZHIKMNOPTYX"

    license_formats = (
        "??? ####",
        "?? ####",
    )

    def license_plate(self) -> str:
        """Generate a license plate."""
        temp = re.sub(
            r"\?",
            lambda x: self.random_element(self.uppercase_letters),
            self.random_element(self.license_formats),
        )
        return self.numerify(temp)
