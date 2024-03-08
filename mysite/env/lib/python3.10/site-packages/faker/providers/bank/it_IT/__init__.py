from .. import Provider as BankProvider


class Provider(BankProvider):
    """Implement bank provider for ``it_IT`` locale."""

    bban_format = "?######################"
    country_code = "IT"
