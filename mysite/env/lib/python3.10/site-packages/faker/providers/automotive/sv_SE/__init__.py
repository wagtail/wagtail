from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    """Implement automotive provider for ``sv_SE`` locale.

    Sources:

    - https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_Sweden
    - https://www.transportstyrelsen.se/en/road/Vehicles/license-plates/
    """

    license_formats = (
        # Classic format
        "??? ###",
        # New format
        "??? ##?",
    )
