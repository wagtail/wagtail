import re
import string

from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    """Implement automotive provider for `nl_NL` locale.

    Sources:
    - https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_the_Netherlands
    - https://www.cbs.nl/en-gb/figures/detail/82044eng

    .. |license_plate_car| replace::
       :meth:`license_plate_car() <faker.providers.automotive.nl_NL.Provider.license_plate_car>`

    .. |license_plate_motorbike| replace::
       :meth:`license_plate_motorbike() <faker.providers.automotive.nl_NL.Provider.license_plate_motorbike>`
    """

    # License formats for cars / other vehicles than motorbikes
    license_formats = (
        # Format 6
        "##-%?-??",
        # Format 7
        "##-%??-#",
        # Format 8
        "#-@??-##",
        # Format 9
        "%?-###-?",
        # Format 10
        "%-###-??",
    )

    # License formats for motorbikes.
    # According to CBS, approximately 10% of road vehicles in the Netherlands are motorbikes
    license_formats_motorbike = (
        "M?-??-##",
        "##-M?-??",
    )

    # Base first letters of format
    license_plate_prefix_letters = "BDFGHJKLNPRSTVXZ"

    # For Format 8 (9-XXX-99) "BDFGHJLNPR" are not used,
    # as to not clash with former export license plates
    license_plate_prefix_letters_format_8 = "KSTVXZ"

    def license_plate_motorbike(self) -> str:
        """Generate a license plate for motorbikes."""
        return self.bothify(
            self.random_element(self.license_formats_motorbike),
            letters=string.ascii_uppercase,
        )

    def license_plate_car(self) -> str:
        """Generate a license plate for cars."""
        # Replace % with license_plate_prefix_letters
        temp = re.sub(
            r"\%",
            self.random_element(self.license_plate_prefix_letters),
            self.random_element(self.license_formats),
        )

        # Replace @ with license_plate_prefix_letters_format_8
        temp = re.sub(r"\@", self.random_element(self.license_plate_prefix_letters_format_8), temp)

        return self.bothify(temp, letters=string.ascii_uppercase)

    def license_plate(self) -> str:
        """Generate a license plate.
        This method randomly chooses 10% between |license_plate_motorbike|
        or 90% |license_plate_car| to generate the result.
        """
        if self.generator.random.random() < 0.1:
            return self.license_plate_motorbike()
        return self.license_plate_car()
