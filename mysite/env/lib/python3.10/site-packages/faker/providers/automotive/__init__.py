import re

from string import ascii_uppercase

from .. import BaseProvider, ElementsType

localized = True


def calculate_vin_str_weight(s: str, weight_factor: list) -> int:
    """
    multiply s(str) by weight_factor char by char
    e.g.
    input: s="ABCDE", weight_factor=[1, 2, 3, 4, 5]
    return: A*1 + B*2 + C*3 + D*4 + E*5

    will multiply 0 when len(weight_factor) less than len(s)
    """

    def _get_char_weight(c: str) -> int:
        """A=1, B=2, ...., I=9,
        J=1, K=2, ..., R=9,
        S=2, T=3, ..., Z=9
        """
        if ord(c) <= 64:  # 0-9
            return int(c)
        if ord(c) <= 73:  # A-I
            return ord(c) - 64
        if ord(c) <= 82:  # J-R
            return ord(c) - 73
        # S-Z
        return ord(c) - 81

    res = 0
    for i, c in enumerate(s):
        res += _get_char_weight(c) * weight_factor[i] if i < len(weight_factor) else 0
    return res


class Provider(BaseProvider):
    """Implement default automotive provider for Faker."""

    license_formats: ElementsType = ()

    def license_plate(self) -> str:
        """Generate a license plate."""
        temp = re.sub(
            r"\?",
            lambda x: self.random_element(ascii_uppercase),
            self.random_element(self.license_formats),
        )
        return self.numerify(temp)

    def vin(self) -> str:
        """Generate vin number."""
        vin_chars = "1234567890ABCDEFGHJKLMNPRSTUVWXYZ"  # I, O, Q are restricted
        front_part = self.bothify("????????", letters=vin_chars)
        rear_part = self.bothify("????????", letters=vin_chars)
        front_part_weight = calculate_vin_str_weight(front_part, [8, 7, 6, 5, 4, 3, 2, 10])
        rear_part_weight = calculate_vin_str_weight(rear_part, [9, 8, 7, 6, 5, 4, 3, 2])
        checksum = (front_part_weight + rear_part_weight) % 11
        checksum_char = "X" if checksum == 10 else str(checksum)
        return front_part + checksum_char + rear_part
