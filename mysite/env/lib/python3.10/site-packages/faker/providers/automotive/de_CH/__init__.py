from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    """Implement automotive provider for ``de_CH`` locale.

    Sources:

    - https://de.wikipedia.org/wiki/Kontrollschild_(Schweiz)#Kantone
    """

    __canton = (
        ("AG", "%## ###"),
        ("AR", "%# ###"),
        ("AI", "%# ###"),
        ("BL", "%## ###"),
        ("BS", "%## ###"),
        ("BE", "%## ###"),
        ("FR", "%## ###"),
        ("GE", "%## ###"),
        ("GL", "%# ###"),
        ("GR", "%## ###"),
        ("JU", "%# ###"),
        ("LU", "%## ###"),
        ("NE", "%## ###"),
        ("NW", "%# ###"),
        ("OW", "%# ###"),
        ("SH", "%# ###"),
        ("SZ", "%## ###"),
        ("SO", "%## ###"),
        ("SG", "%## ###"),
        ("TI", "%## ###"),
        ("TG", "%## ###"),
        ("UR", "%# ###"),
        ("VD", "%## ###"),
        ("VS", "%## ###"),
        ("ZG", "%## ###"),
        ("ZH", "%## ###"),
    )

    def license_plate(self) -> str:
        """Generate a license plate."""
        plate: tuple = self.random_element(self.__canton)
        return f"{plate[0]}-{self.numerify(plate[1])}".strip()
