from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    """Implement automotive provider for ``zh_TW`` locale.

    Sources:
    - https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_Taiwan

    """

    license_formats = (
        "####-??",
        "??-####",
        # Commercial vehicles since 2012
        "???-###",
        # New format since 2014
        "???-####",
    )
