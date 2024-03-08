from .. import Provider as BankProvider


class Provider(BankProvider):
    """Implement bank provider for ``en_IN`` locale.
    Source: https://en.wikipedia.org/wiki/List_of_banks_in_India
    """

    banks = (
        "Bank of Baroda",
        "Bank of India",
        "Bank of Maharashtra",
        "Canara Bank",
        "Central Bank of India",
        "Indian Bank",
        "Indian Overseas Bank",
        "Punjab National Bank",
        "Punjab and Sind Bank",
        "Union Bank of India",
        "UCO Bank",
        "State Bank of India",
        "Axis Bank",
        "Bandhan Bank",
        "CSB Bank",
        "City Union Bank",
        "DCB Bank",
        "Dhanlaxmi Bank",
        "Federal Bank",
        "HDFC Bank",
        "ICICI Bank",
        "IDBI Bank",
        "IDFC First Bank",
        "IndusInd Bank",
        "Jammu & Kashmir Bank",
        "Karnataka Bank",
        "Karur Vysya Bank",
        "Kotak Mahindra Bank",
        "Nainital Bank",
        "RBL Bank",
        "South Indian Bank",
        "Tamilnad Mercantile Bank",
        "Yes Bank",
    )

    def bank(self) -> str:
        """Generate a bank name."""
        return self.random_element(self.banks)
