from .. import Provider as BankProvider


class Provider(BankProvider):
    """Implement bank provider for ``en_GB`` locale."""

    bban_format = "????##############"
    country_code = "GB"
