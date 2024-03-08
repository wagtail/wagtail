import re

from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    """Implement automotive provider for ``ar_SA`` locale.

    Sources:

    - https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_Saudi_Arabia

    .. |license_plate_en| replace::
        :meth:`license_plate_en()`
    """

    LICENSE_FORMAT_EN = "#### ???"
    LICENSE_FORMAT_AR = "? ? ? ####"

    PLATE_CHARS_EN = "ABDEGHJKLNRSTUVXZ"
    PLATE_CHARS_AR = "أبدعقهحكلنرسطوىصم"

    PLATE_MAP = {
        "A": "ا",
        "B": "ب",
        "D": "د",
        "E": "ع",
        "G": "ق",
        "H": "ه",
        "J": "ح",
        "K": "ك",
        "L": "ل",
        "N": "ن",
        "R": "ر",
        "S": "س",
        "T": "ط",
        "U": "و",
        "V": "ى",
        "X": "ص",
        "Z": "م",
        "0": "٠",
        "1": "١",
        "2": "٢",
        "3": "٣",
        "4": "٤",
        "5": "٥",
        "6": "٦",
        "7": "٧",
        "8": "٨",
        "9": "٩",
    }

    def license_plate_en(self) -> str:
        """Generate a license plate in Latin/Western characters."""
        return self.bothify(
            self.LICENSE_FORMAT_EN,
            letters=self.PLATE_CHARS_EN,
        )

    def license_plate_ar(self) -> str:
        """Generate a license plate in Arabic characters.

        This method first generates a license plate in Latin/Western characters
        using |license_plate_en|, and the result is translated internally to
        generate the Arabic counterpart which serves as this method's return
        value.
        """
        english_plate = self.license_plate_en()
        return self._translate_license_plate(english_plate)

    def _translate_license_plate(self, license_plate: str) -> str:
        nums = list(reversed(license_plate[0:4]))
        chars = list(license_plate[5:8])

        numerated = re.sub(
            r"\#",
            lambda x: self.PLATE_MAP[nums.pop()],
            self.LICENSE_FORMAT_AR,
        )
        ar_plate = re.sub(
            r"\?",
            lambda x: self.PLATE_MAP[chars.pop()],
            numerated,
        )

        return ar_plate

    def license_plate(self, ar: bool = True) -> str:
        return self.license_plate_ar() if ar else self.license_plate_en()
