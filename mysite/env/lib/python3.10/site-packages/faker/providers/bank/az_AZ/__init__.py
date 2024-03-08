from .. import Provider as BankProvider


class Provider(BankProvider):
    """Implement bank provider for ``az_AZ`` locale."""

    bban_format = "????####################"
    country_code = "AZ"

    banks = (
        "AccessBank",
        "AFB Bank",
        "Azərbaycan Sənaye Bankı",
        "Azər Türk Bank",
        "Bank Avrasiya",
        "Bank BTB",
        "Bank Melli Iran",
        "Bank of Baku",
        "Bank Respublika",
        "Expressbank",
        "Günay Bank",
        "Kapital Bank",
        "MuğanBank",
        "Naxçıvan Bank",
        "National Bank of Pakistan",
        "PAŞA Bank",
        "Premium Bank",
        "Rabitəbank",
        "TuranBank",
        "Unibank",
        "VTB Bank",
        "Xalq Bank",
        "Yapıkredi Bank Azərbaycan",
        "Yelo Bank",
        "Ziraat Bank Azərbaycan",
    )

    def bank(self):
        """Generate a bank name."""
        return self.random_element(self.banks)
