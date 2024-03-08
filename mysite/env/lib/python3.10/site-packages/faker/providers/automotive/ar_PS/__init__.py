from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    """Implement automotive provider for ``ar_PS`` locale.

    Sources:

    - https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_the_Palestinian_National_Authority
    """

    license_formats = (
        # Private vehicles
        "{{district}}-####-3#",
        "{{district}}-####-4#",
        "{{district}}-####-7#",
        "{{district}}-####-9#",
        # Public transport
        "{{district}}-####-30",
        # Authority vehicles
        "####",
        # New police vehicles
        "####-99",
        # Gaza strip after 2012
        # Private
        "1-####-0#",
        "3-####-0#",
        # Commercial
        "1-####-1#",
        "3-####-1#",
        # Public
        "1-####-2#",
        "3-####-2#",
        # Municipal
        "1-####-4#",
        "3-####-4#",
        # Governmental, and Governmental personal vehicles
        "1-####-5#",
        "3-####-5#",
    )

    def district(self) -> str:
        """Generate a district code for license plates."""
        return self.random_element(
            [
                # Gaza Strip
                "1",
                "3",
                # Northern West Bank (Nablus, Tulkarm, Qalqilya, Jenin)
                "4",
                "7",
                # Central West Bank (Ramallah, Jerusalem, Jericho)
                "5",
                "6",
                # Southern West Bank (Bethlehem, Hebron)
                "8",
                "9",
            ]
        )

    def license_plate(self) -> str:
        """Generate a license plate."""
        pattern: str = self.random_element(self.license_formats)
        return self.numerify(self.generator.parse(pattern))
