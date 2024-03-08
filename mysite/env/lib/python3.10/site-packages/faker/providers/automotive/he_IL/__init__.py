from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    """Implement automotive provider for ``he_IL`` locale."""

    """ Source : https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_Israel  """
    license_formats = (
        "###-##-###",
        "##-###-##",
    )
