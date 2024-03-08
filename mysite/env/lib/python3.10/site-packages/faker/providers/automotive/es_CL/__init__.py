# -*- coding: utf-8 -*-

import re

from collections import OrderedDict

from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    """Implement automotive provider for ``es`` locale.

    Sources:

    - https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_Chile

    """

    license_plate_old_format_first_letters = "ABCDFGHJKLPRSTVWXYZ"
    license_plate_old_format_second_letters = "ABCDFGHIJKLPRSTVWXYZ"
    license_plate_new_format_letters = "BCDFGHJKLPRSTVWXYZ"

    license_formats = OrderedDict(
        [
            ("{{license_plate_new}}", 0.70),
            ("{{license_plate_old}}", 0.20),
            ("{{license_plate_police}}", 0.05),
            ("{{license_plate_temporary}}", 0.04),
            ("{{license_plate_diplomatic}}", 0.01),
        ]
    )

    def license_plate_old(self) -> str:
        """Generate an old format license plate."""
        format = "-####"

        letters = "".join(
            (
                self.random_element(self.license_plate_old_format_first_letters),
                self.random_element(self.license_plate_old_format_second_letters),
            )
        )

        return self.numerify(letters + format)

    def license_plate_new(self) -> str:
        format = "????-##"

        temp = re.sub(r"\?", lambda x: self.random_element(self.license_plate_new_format_letters), format)
        return self.numerify(temp)

    def license_plate_police(self) -> str:
        formats = ("RP-####", "Z-####")
        return self.numerify(self.random_element(formats))

    def license_plate_temporary(self) -> str:
        format = "PR-###"
        return self.numerify(format)

    def license_plate_diplomatic(self) -> str:
        formats = ("CC-####", "CD-####")
        return self.numerify(self.random_element(formats))

    def license_plate(self) -> str:
        """Generate a license plate."""
        return self.numerify(self.generator.parse(self.random_element(self.license_formats)))
