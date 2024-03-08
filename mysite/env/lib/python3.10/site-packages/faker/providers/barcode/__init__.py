from typing import Tuple, Union

from .. import BaseProvider

localized = True

PrefixType = Tuple[Union[int, str, Tuple[Union[int, str], ...]], ...]


class Provider(BaseProvider):
    """Implement default barcode provider for Faker.

    Sources:

    - https://gs1.org/standards/id-keys/company-prefix
    """

    local_prefixes: PrefixType = ()

    def _ean(self, length: int = 13, prefixes: PrefixType = ()) -> str:
        if length not in (8, 13):
            raise AssertionError("length can only be 8 or 13")

        code = [self.random_digit() for _ in range(length - 1)]

        if prefixes:
            prefix: str = self.random_element(prefixes)  # type: ignore[assignment]
            code[: len(prefix)] = map(int, prefix)

        if length == 8:
            weights = [3, 1, 3, 1, 3, 1, 3]
        elif length == 13:
            weights = [1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3]

        weighted_sum = sum(x * y for x, y in zip(code, weights))
        check_digit = (10 - weighted_sum % 10) % 10
        code.append(check_digit)

        return "".join(str(x) for x in code)

    def ean(self, length: int = 13, prefixes: PrefixType = ()) -> str:
        """Generate an EAN barcode of the specified ``length``.

        The value of ``length`` can only be ``8`` or ``13`` (default) which will
        create an EAN-8 or an EAN-13 barcode respectively.

        If a value for ``prefixes`` is specified, the result will begin with one
        of the sequences in ``prefixes``.

        :sample: length=13
        :sample: length=8
        :sample: prefixes=('00',)
        :sample: prefixes=('45', '49')
        """
        return self._ean(length, prefixes=prefixes)

    def ean8(self, prefixes: PrefixType = ()) -> str:
        """Generate an EAN-8 barcode.

        This method uses |ean| under the hood with the ``length`` argument
        explicitly set to ``8``.

        If a value for ``prefixes`` is specified, the result will begin with one
        of the sequences in ``prefixes``.

        :sample:
        :sample: prefixes=('00',)
        :sample: prefixes=('45', '49')
        """
        return self._ean(8, prefixes=prefixes)

    def ean13(self, prefixes: PrefixType = ()) -> str:
        """Generate an EAN-13 barcode.

        This method uses |ean| under the hood with the ``length`` argument
        explicitly set to ``13``.

        If a value for ``prefixes`` is specified, the result will begin with one
        of the sequences in ``prefixes``.

        .. note::
           Codes starting with a leading zero are treated specially in some
           barcode readers. For more information on compatibility with UPC-A
           codes, see |EnUsBarcodeProvider.ean13|.

        :sample:
        :sample: prefixes=('00',)
        :sample: prefixes=('45', '49')
        """
        return self._ean(13, prefixes=prefixes)

    def localized_ean(self, length: int = 13) -> str:
        """Generate a localized EAN barcode of the specified ``length``.

        The value of ``length`` can only be ``8`` or ``13`` (default) which will
        create an EAN-8 or an EAN-13 barcode respectively.

        This method uses the standard barcode provider's |ean| under the hood
        with the ``prefixes`` argument explicitly set to ``local_prefixes`` of
        a localized barcode provider implementation.

        :sample:
        :sample: length=13
        :sample: length=8
        """
        return self._ean(length, prefixes=self.local_prefixes)

    def localized_ean8(self) -> str:
        """Generate a localized EAN-8 barcode.

        This method uses |localized_ean| under the hood with the ``length``
        argument explicitly set to ``8``.
        """
        return self.localized_ean(8)

    def localized_ean13(self) -> str:
        """Generate a localized EAN-13 barcode.

        This method uses |localized_ean| under the hood with the ``length``
        argument explicitly set to ``13``.
        """
        return self.localized_ean(13)
