from .. import Provider as BankProvider


class Provider(BankProvider):
    """Implement bank provider for ``no_NO`` locale."""

    bban_format = "###########"
    country_code = "NO"
