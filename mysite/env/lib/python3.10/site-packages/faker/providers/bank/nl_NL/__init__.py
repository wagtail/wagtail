from .. import Provider as BankProvider


class Provider(BankProvider):
    """Implement bank provider for ``nl_NL`` locale."""

    bban_format = "????##########"
    country_code = "NL"
