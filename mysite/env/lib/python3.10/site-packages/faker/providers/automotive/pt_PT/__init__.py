from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    """Implement automotive provider for ``pt_PT`` locale.

    Sources:

    - https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_Portugal
    """

    license_formats = (
        "##-##-??",
        "##-??-##",
        "??-##-##",
        # New format since March 2020
        "??-##-??",
    )
