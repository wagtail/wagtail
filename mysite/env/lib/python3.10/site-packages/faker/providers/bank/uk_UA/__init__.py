from .. import Provider as BankProvider


class Provider(BankProvider):
    """Implement bank provider for ``uk_UA`` locale.
    Source for rules for bban format:
    https://bank.gov.ua/en/iban
    """

    bban_format = "#" * 27
    country_code = "UA"
