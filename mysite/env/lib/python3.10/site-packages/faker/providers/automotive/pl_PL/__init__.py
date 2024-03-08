from typing import List

from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    """Implement automotive provider for ``pl_PL`` locale.

    Sources:

    - https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_Poland
    """

    license_formats = (
        "?? #####",
        "?? ####?",
        "?? ###??",
        "?? #?###",
        "?? #??##",
        "??? ?###",
        "??? ##??",
        "??? #?##",
        "??? ##?#",
        "??? #??#",
        "??? ??##",
        "??? #####",
        "??? ####?",
        "??? ###??",
    )

    def license_plate_regex_formats(self) -> List[str]:
        """Return a regex for matching license plates.

        .. warning::
           This is technically not a method that generates fake data, and it
           should not be part of the public API. User should refrain from using
           this method.
        """
        return [plate.replace("?", "[A-Z]").replace("#", "[0-9]") for plate in self.license_formats]
