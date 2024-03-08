from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    """Implement automotive provider for ``lt_LT`` locale.

    Source:

    - https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_Lithuania
    """

    license_formats = ("??? ###",)
