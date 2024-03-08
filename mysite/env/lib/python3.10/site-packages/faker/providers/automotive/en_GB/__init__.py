from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    """Implement automotive provider for ``en_GB`` locale.

    Sources:

    - https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_the_United_Kingdom
    """

    license_formats = (
        "??## ???",
        "??##???",
    )
