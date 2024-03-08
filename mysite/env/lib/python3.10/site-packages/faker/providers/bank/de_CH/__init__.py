from .. import Provider as BankProvider


class Provider(BankProvider):
    """Implement bank provider for ``de_CH`` locale."""

    bban_format = "#################"
    country_code = "CH"
