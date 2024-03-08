from faker.providers.currency import Provider as CurrencyProvider


class Provider(CurrencyProvider):
    price_formats = ["#,##", "%#,##", "%##,##", "%.###,##", "%#.###,##"]

    def pricetag(self) -> str:
        return "\N{euro sign}" + self.numerify(self.random_element(self.price_formats))
