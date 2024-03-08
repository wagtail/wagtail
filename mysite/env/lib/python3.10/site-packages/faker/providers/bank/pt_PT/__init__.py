from .. import Provider as BankProvider


class Provider(BankProvider):
    """Implement bank provider for ``pt_PT`` locale."""

    bban_format = "#####################"
    country_code = "PT"
