from .. import Provider as BankProvider


class Provider(BankProvider):
    """Implement bank provider for ``tr_TR`` locale."""

    bban_format = "######################"
    country_code = "TR"
