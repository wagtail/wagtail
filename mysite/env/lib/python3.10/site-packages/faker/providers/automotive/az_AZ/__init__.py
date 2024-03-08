import re

from .. import Provider as AutoProvider


class Provider(AutoProvider):
    """Implement license formats for ``az_AZ`` locale."""

    license_formats = ("##-??-###",)
    ascii_uppercase_azerbaijan = "ABCDEFGHXIJKQLMNOPRSTUVYZ"
    license_plate_initial_numbers = (
        "01",
        "02",
        "03",
        "04",
        "05",
        "06",
        "07",
        "08",
        "09",
        "10",
        "90",
        "11",
        "12",
        "14",
        "15",
        "16",
        "17",
        "18",
        "19",
        "20",
        "21",
        "22",
        "23",
        "24",
        "25",
        "26",
        "27",
        "28",
        "29",
        "30",
        "31",
        "32",
        "33",
        "34",
        "35",
        "36",
        "37",
        "38",
        "39",
        "40",
        "41",
        "42",
        "43",
        "44",
        "45",
        "46",
        "47",
        "48",
        "49",
        "50",
        "51",
        "52",
        "53",
        "54",
        "55",
        "56",
        "57",
        "58",
        "59",
        "60",
        "61",
        "62",
        "63",
        "64",
        "65",
        "66",
        "67",
        "68",
        "69",
        "70",
        "71",
        "72",
        "77",
        "85",
    )

    def license_plate(self) -> str:
        """Generate a license plate."""
        temp = re.sub(
            r"\?",
            lambda x: self.random_element(self.ascii_uppercase_azerbaijan),
            self.random_element(self.license_formats),
        )
        temp = temp.replace("##", self.random_element(self.license_plate_initial_numbers), 1)
        # temp = temp.format(self.random_element(range(1, 999)))
        return self.numerify(temp)
