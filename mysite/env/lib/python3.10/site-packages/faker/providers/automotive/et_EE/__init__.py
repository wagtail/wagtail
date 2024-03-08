from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    """Implement automotive provider for ``et_EE`` locale.

    Source:

    - https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_Estonia
    """

    license_formats = ("### ???",)
