from .. import Provider as BankProvider


class Provider(BankProvider):
    """Implement bank provider for ``en_IE`` locale."""

    bban_format = "#######################"
    country_code = "IE"
