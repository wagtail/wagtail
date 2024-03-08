from collections import OrderedDict
from string import ascii_uppercase

from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    """Implement automotive provider for ``es_AR`` locale.

    Sources:

    - https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_Argentina

    """

    license_plate_old_format_first_letter = ascii_uppercase.replace("YZ", "")

    license_plate_new_first_letter = OrderedDict(
        [
            ("A", 0.99),
            ("B", 0.001),
            ("C", 0.0001),
            ("D", 0.00001),
            ("E", 0.0000000001),
        ]
    )

    license_plate_new_second_letter = OrderedDict(
        [
            ("A", 0.1),
            ("B", 0.1),
            ("C", 0.1),
            ("D", 0.1),
            ("E", 0.1),
            ("F", 0.1),
            ("G", 0.09),
            ("H", 0.08),
            ("I", 0.07),
            ("J", 0.06),
            ("K", 0.04),
            ("L", 0.03),
            ("M", 0.009),
            ("N", 0.007),
            ("O", 0.005),
            ("P", 0.004),
            ("Q", 0.001),
            ("R", 0.0009),
            ("S", 0.0008),
            ("T", 0.0007),
            ("U", 0.0006),
            ("V", 0.0005),
            ("W", 0.0003),
            ("X", 0.0002),
            ("Y", 0.0001),
            ("Z", 0.00005),
        ]
    )

    license_formats = OrderedDict(
        [
            ("{{license_plate_old}}", 0.6),
            ("{{license_plate_mercosur}}", 0.4),
        ]
    )

    def license_plate_old(self) -> str:
        """Generate an old format license plate. Since 1995 to 2016"""
        format = "??###"

        first_letter: str = self.random_element(self.license_plate_old_format_first_letter)

        return self.bothify(first_letter + format).upper()

    def license_plate_mercosur(self) -> str:
        """Generate an new plate with Mercosur format. Since 2016"""

        first_letter: str = self.random_element(self.license_plate_new_first_letter)
        second_letter: str = self.random_element(self.license_plate_new_second_letter)

        format = "###??"
        plate = first_letter + second_letter

        return self.bothify(plate + format).upper()

    def license_plate(self) -> str:
        """Generate a license plate."""
        return self.numerify(self.generator.parse(self.random_element(self.license_formats)))
