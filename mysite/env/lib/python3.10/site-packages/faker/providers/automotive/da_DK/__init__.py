from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    """Implement automotive provider for ``da_DK`` locale.
    Source: https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_Denmark
    """

    license_formats = ("?? ## ###",)
