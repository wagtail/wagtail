from ..es import Provider as CurrencyProvider


class Provider(CurrencyProvider):
    price_formats = ["%##", "%.###", "%#.##0", "%##.##0", "%##.##0", "%.###.##0"]

    def pricetag(self) -> str:
        return "\N{dollar sign}\N{no-break space}" + self.numerify(self.random_element(self.price_formats))
