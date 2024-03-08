from .. import Provider as BankProvider


class Provider(BankProvider):
    """Implement bank provider for ``nl_BE`` locale.

    Information about the Belgian banks can be found on the website
    of the National Bank of Belgium:
    https://www.nbb.be/nl/betalingen-en-effecten/betalingsstandaarden/bankidentificatiecodes
    """

    bban_format = "############"
    country_code = "BE"

    banks = (
        "Argenta Spaarbank",
        "AXA Bank",
        "Belfius Bank",
        "BNP Paribas Fortis",
        "Bpost Bank",
        "Crelan",
        "Deutsche Bank AG",
        "ING België",
        "KBC Bank",
    )
    swift_bank_codes = (
        "ARSP",
        "AXAB",
        "BBRU",
        "BPOT",
        "DEUT",
        "GEBA",
        "GKCC",
        "KRED",
        "NICA",
    )
    swift_location_codes = (
        "BE",
        "B2",
        "99",
        "21",
        "91",
        "23",
        "3X",
        "75",
        "2X",
        "22",
        "88",
        "B1",
        "BX",
        "BB",
    )
    swift_branch_codes = [
        "203",
        "BTB",
        "CIC",
        "HCC",
        "IDJ",
        "IPC",
        "MDC",
        "RET",
        "VOD",
        "XXX",
    ]

    def bank(self) -> str:
        """Generate a bank name."""
        return self.random_element(self.banks)
