from .. import Provider as BarcodeProvider


class Provider(BarcodeProvider):
    """Implement barcode provider for ``ja_JP`` locale.

    Japanese local EAN barcodes are called JAN-codes.

    Sources:

    - https://gs1.org/standards/id-keys/company-prefix
    - https://www.dsri.jp/jan/about_jan.html

    .. |JaJpProvider.localized_ean| replace::
       :meth:`JaJpProvider.localized_ean() <faker.providers.barcode.ja_JP.Provider.localized_ean>`

    .. |JaJpProvider.localized_ean8| replace::
       :meth:`JaJpProvider.localized_ean8() <faker.providers.barcode.ja_JP.Provider.localized_ean8>`

    .. |JaJpProvider.localized_ean13| replace::
       :meth:`JaJpProvider.localized_ean13() <faker.providers.barcode.ja_JP.Provider.localized_ean13>`
    """

    local_prefixes = (4, 5), (4, 9)

    def jan(self, length: int = 13) -> str:
        """Generate a JAN barcode of the specified ``length``.

        This method is an alias for |JaJpProvider.localized_ean|.

        :sample:
        :sample: length=8
        :sample: length=13
        """
        return self.localized_ean(length)

    def jan8(self) -> str:
        """Generate a 8 digit JAN barcode.

        This method is an alias for |JaJpProvider.localized_ean8|.
        """
        return self.localized_ean8()

    def jan13(self) -> str:
        """Generate a 13 digit JAN barcode.

        This method is an alias for |JaJpProvider.localized_ean13|.
        """
        return self.localized_ean13()
