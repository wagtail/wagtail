from .. import Provider as BankProvider


class Provider(BankProvider):
    """Implement bank provider for ``cs_CZ`` locale.

    https://www.mbank.cz/informace-k-produktum/info/ucty/cislo-uctu-iban.html
    """

    bban_format = "####################"
    country_code = "CZ"
