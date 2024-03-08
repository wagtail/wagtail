from .. import Provider as BankProvider


class Provider(BankProvider):
    """Implement bank provider for ``sk_SK`` locale.

    https://www.mbank.cz/informace-k-produktum/info/ucty/cislo-uctu-iban.html
    """

    bban_format = "####################"
    country_code = "SK"
