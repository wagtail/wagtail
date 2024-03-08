from collections import OrderedDict

from ..en import Provider as AddressProvider


class Provider(AddressProvider):
    counties = (
        "Cork",
        "Galway",
        "Mayo",
        "Donegal",
        "Kerry",
        "Tipperary",
        "Clare",
        "Tyrone",
        "Antrim",
        "Limerick",
        "Roscommon",
        "Down",
        "Meath",
        "Londonderry",
        "Wexford",
        "Kilkenny",
        "Offaly",
        "Cavan",
        "Wicklow",
        "Waterford",
        "Sligo",
        "Laois",
        "Westmeath",
        "Kildare",
        "Leitrim",
        "Armagh",
        "Fermanagh",
        "Monaghan",
        "Dublin",
        "Louth",
        "Longford",
        "Carlow",
    )

    _postcode_sets = OrderedDict(
        (
            (" ", [" ", ""]),
            ("N", [str(i) for i in range(0, 10)]),
            ("L", "ACDEFHKNPRTVWXY"),
            ("A", "ACDEFHKNPRTVWXY0123456789"),
        )
    )
    postcode_pattern: str = "LNN AAAA"

    def postcode(self) -> str:
        postcode = ""
        for placeholder in self.postcode_pattern:
            postcode += self.random_element(self._postcode_sets[placeholder])
        return postcode

    def administrative_unit(self) -> str:
        return self.random_element(self.counties)

    county = administrative_unit
