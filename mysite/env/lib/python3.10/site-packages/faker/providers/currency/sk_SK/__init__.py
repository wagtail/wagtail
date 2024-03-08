from .. import Provider as CurrencyProvider


class Provider(CurrencyProvider):
    price_formats = ["#,##", "%#,##", "%##,##", "%.###,##", "%#.###,##"]

    def pricetag(self):
        return self.numerify(self.random_element(self.price_formats)) + "\N{no-break space}\N{euro sign}"
