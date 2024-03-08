from .. import Provider as BankProvider


class Provider(BankProvider):
    """Implement bank provider for ``fr_FR`` locale."""

    bban_format = "#######################"
    country_code = "FR"
