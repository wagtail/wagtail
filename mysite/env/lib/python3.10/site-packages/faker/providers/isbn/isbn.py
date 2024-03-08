"""
This module is responsible for generating the check digit and formatting
ISBN numbers.
"""
from typing import Any, Optional


class ISBN:
    MAX_LENGTH = 13

    def __init__(
        self,
        ean: Optional[str] = None,
        group: Optional[str] = None,
        registrant: Optional[str] = None,
        publication: Optional[str] = None,
    ) -> None:
        self.ean = ean
        self.group = group
        self.registrant = registrant
        self.publication = publication


class ISBN13(ISBN):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.check_digit = self._check_digit()

    def _check_digit(self) -> str:
        """Calculate the check digit for ISBN-13.
        See https://en.wikipedia.org/wiki/International_Standard_Book_Number
        for calculation.
        """
        weights = (1 if x % 2 == 0 else 3 for x in range(12))
        body = "".join([part for part in [self.ean, self.group, self.registrant, self.publication] if part is not None])
        remainder = sum(int(b) * w for b, w in zip(body, weights)) % 10
        diff = 10 - remainder
        check_digit = 0 if diff == 10 else diff
        return str(check_digit)

    def format(self, separator: str = "") -> str:
        return separator.join(
            [
                part
                for part in [
                    self.ean,
                    self.group,
                    self.registrant,
                    self.publication,
                    self.check_digit,
                ]
                if part is not None
            ]
        )


class ISBN10(ISBN):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.check_digit = self._check_digit()

    def _check_digit(self) -> str:
        """Calculate the check digit for ISBN-10.
        See https://en.wikipedia.org/wiki/International_Standard_Book_Number
        for calculation.
        """
        weights = range(1, 10)
        body = "".join([part for part in [self.group, self.registrant, self.publication] if part is not None])
        remainder = sum(int(b) * w for b, w in zip(body, weights)) % 11
        check_digit = "X" if remainder == 10 else str(remainder)
        return str(check_digit)

    def format(self, separator: str = "") -> str:
        return separator.join(
            [
                part
                for part in [
                    self.group,
                    self.registrant,
                    self.publication,
                    self.check_digit,
                ]
                if part is not None
            ]
        )
