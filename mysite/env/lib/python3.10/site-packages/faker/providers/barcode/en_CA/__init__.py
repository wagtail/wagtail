from itertools import product

from ..en_US import Provider as EnUsBarcodeProvider


class Provider(EnUsBarcodeProvider):
    """Implement barcode provider for ``en_CA`` locale.

    Canada uses UPC as well, so there are similarities between this and the
    ``en_US`` implementation.

    Sources:

    - https://gs1.org/standards/id-keys/company-prefix
    - https://www.nationwidebarcode.com/upc-country-codes/
    """

    local_prefixes = (
        # Some sources do not specify prefixes 00~01, 06~09 for use in Canada,
        # but it's referenced in other pages
        *product((0,), range(2)),
        *product((0,), range(6, 10)),
        (7, 5),
    )
