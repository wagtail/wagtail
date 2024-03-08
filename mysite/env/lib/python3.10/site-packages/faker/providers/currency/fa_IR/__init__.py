from .. import Provider as CurrencyProvider


class Provider(CurrencyProvider):
    price_formats = ["###,###,000", "#,###,000,000", "%,###,###,###,###", "%,###,###,###,000,000"]

    def pricetag(self) -> str:
        return self.numerify(self.random_element(self.price_formats)) + "\uFDFC"
