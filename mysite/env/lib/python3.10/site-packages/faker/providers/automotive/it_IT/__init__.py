from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    """Implement automotive provider for ``it_IT`` locale.

    Sources:

    - https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_Italy
    """

    license_formats = (
        # 1994-present
        "??###??",
    )
