from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    """Implement automotive provider for ``ar_BH`` locale.

    Source:

    - https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_Bahrain
    """

    license_formats = ("######",)
