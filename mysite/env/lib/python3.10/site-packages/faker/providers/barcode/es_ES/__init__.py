from .. import Provider as BarcodeProvider


class Provider(BarcodeProvider):
    """Implement barcode provider for ``es_ES`` locale.

    Sources:

    - https://gs1.org/standards/id-keys/company-prefix
    """

    local_prefixes = ((8, 4),)
