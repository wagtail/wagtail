import string

from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    """Implement automotive provider for ``ro_RO`` locale."""

    license_plate_prefix = (
        "AB",
        "AG",
        "AR",
        "B",
        "BC",
        "BH",
        "BN",
        "BR",
        "BT",
        "BV",
        "BZ",
        "CJ",
        "CL",
        "CS",
        "CT",
        "CV",
        "DB",
        "DJ",
        "GJ",
        "GL",
        "GR",
        "HD",
        "HR",
        "IF",
        "IL",
        "IS",
        "MH",
        "MM",
        "MS",
        "NT",
        "OT",
        "PH",
        "SB",
        "SJ",
        "SM",
        "SV",
        "TL",
        "TM",
        "TR",
        "VL",
        "VN",
        "VS",
    )

    license_plate_suffix = (
        "-###-???",
        "-##-???",
    )

    def license_plate(self) -> str:
        """Generate a license plate."""
        prefix: str = self.random_element(self.license_plate_prefix)
        suffix = self.bothify(
            self.random_element(self.license_plate_suffix),
            letters=string.ascii_uppercase,
        )
        return prefix + suffix
