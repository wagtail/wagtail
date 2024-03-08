from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    """Implement automotive provider for ``fi_FI`` locale.

    Source:

    - https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_Finland
    """

    license_formats = ("???-###",)
