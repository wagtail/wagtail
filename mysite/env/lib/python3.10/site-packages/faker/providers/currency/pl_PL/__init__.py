from .. import Provider as CurrencyProvider


class Provider(CurrencyProvider):
    price_formats = ["#,##", "%#,##", "%##,##", "%.###,##", "%#.###,##"]

    def pricetag(self) -> str:
        return self.numerify(self.random_element(self.price_formats)) + "\N{no-break space}zł"
