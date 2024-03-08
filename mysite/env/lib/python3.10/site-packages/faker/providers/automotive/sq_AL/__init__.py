from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    """Implement automotive provider for ``sq_AL`` locale.

    Source:

    - https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_Albania
    """

    license_formats = ("?? ###??",)
