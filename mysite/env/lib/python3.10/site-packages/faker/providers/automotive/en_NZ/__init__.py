from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    """Implement automotive provider for ``en_NZ`` locale.

    Sources:

    - https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_New_Zealand
    """

    license_formats = (
        # Old plates
        "??%##",
        "??%###",
        "??%###",
        # Three letters since 2002
        "A??%##",
        "B??%##",
        "C??%##",
        "D??%##",
        "E??%##",
        "F??%##",
        "G??%##",
        "H??%##",
        "J??%##",
        "K??%##",
        "L??%##",
        "M??%##",
        # After 2018
        "N??%##",
    )
