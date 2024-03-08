from typing import Tuple

from ..de import Provider as AddressProvider


class Provider(AddressProvider):
    city_formats = ("{{city_name}}",)
    building_number_formats = ("%", "%#", "%#", "%#", "%##")
    street_suffixes = ["strasse"]
    street_name_formats = ("{{last_name}}{{street_suffix}}",)
    street_address_formats = ("{{street_name}} {{building_number}}",)
    address_formats = ("{{street_address}}\n{{postcode}} {{city}}",)
    postcode_formats = (
        "1###",
        "2###",
        "3###",
        "4###",
        "5###",
        "6###",
        "7###",
        "8###",
        "9###",
    )

    cities = (
        "Aarau",
        "Adliswil",
        "Aesch",
        "Affoltern",
        "Aigle",
        "Allschwil",
        "Altstätten",
        "Amriswil",
        "Arbon",
        "Arth",
        "Baar",
        "Baden",
        "Basel",
        "Bassersdorf",
        "Bellinzona",
        "Belp",
        "Bern",
        "Bernex",
        "Biel/Bienne",
        "Binningen",
        "Birsfelden",
        "Brig-Glis",
        "Brugg",
        "Buchs",
        "Bülach",
        "Bulle",
        "Burgdorf",
        "Carouge",
        "Cham",
        "Chêne-Bougeries",
        "Chur",
        "Crans-Montana",
        "Davos",
        "Delsberg",
        "Dietikon",
        "Dübendorf",
        "Ebikon",
        "Ecublens",
        "Einsiedeln",
        "Emmen",
        "Flawil",
        "Frauenfeld",
        "Freiburg",
        "Freienbach",
        "Genf",
        "Gland",
        "Glarus",
        "Glarus",
        "Gossau",
        "Gossau",
        "Grenchen",
        "Herisau",
        "Hinwil",
        "Horgen",
        "Horw",
        "Illnau-Effretikon",
        "Ittigen",
        "Kloten",
        "Köniz",
        "Kreuzlingen",
        "Kriens",
        "Küsnacht",
        "Küssnacht",
        "La Chaux-de-Fonds",
        "La Tour-de-Peilz",
        "Lancy",
        "Langenthal",
        "Lausanne",
        "Le Grand-Saconnex",
        "Lenzburg",
        "Liestal",
        "Locarno",
        "Lugano",
        "Lutry",
        "Luzern",
        "Lyss",
        "Männedorf",
        "Martigny",
        "Maur",
        "Meilen",
        "Mendrisio",
        "Meyrin",
        "Möhlin",
        "Monthey",
        "Montreux",
        "Morges",
        "Münchenbuchsee",
        "Münchenstein",
        "Münsingen",
        "Muri",
        "Muttenz",
        "Naters",
        "Neuenburg",
        "Neuhausen",
        "Nyon",
        "Oberwil",
        "Oftringen",
        "Olten",
        "Onex",
        "Opfikon",
        "Ostermundigen",
        "Payerne",
        "Pfäffikon",
        "Plan-les-Ouates",
        "Pratteln",
        "Prilly",
        "Pully",
        "Rapperswil-Jona",
        "Regensdorf",
        "Reinach",
        "Renens",
        "Rheinfelden",
        "Richterswil",
        "Riehen",
        "Risch",
        "Romanshorn",
        "Rüti",
        "Sarnen",
        "Schaffhausen",
        "Schlieren",
        "Schwyz",
        "Siders",
        "Sitten",
        "Solothurn",
        "Spiez",
        "Spreitenbach",
        "St. Gallen",
        "Stäfa",
        "Steffisburg",
        "Steinhausen",
        "Suhr",
        "Sursee",
        "Thalwil",
        "Thônex",
        "Thun",
        "Urdorf",
        "Uster",
        "Uzwil",
        "Val-de-Ruz",
        "Val-de-Travers",
        "Vernier",
        "Versoix",
        "Vevey",
        "Veyrier",
        "Villars-sur-Glâne",
        "Volketswil",
        "Wädenswil",
        "Wald",
        "Wallisellen",
        "Weinfelden",
        "Wettingen",
        "Wetzikon",
        "Wil",
        "Winterthur",
        "Wohlen",
        "Worb",
        "Yverdon-les-Bains",
        "Zofingen",
        "Zollikofen",
        "Zollikon",
        "Zug",
        "Zürich",
    )

    cantons = (
        ("AG", "Aargau"),
        ("AI", "Appenzell Innerrhoden"),
        ("AR", "Appenzell Ausserrhoden"),
        ("BE", "Bern"),
        ("BL", "Basel-Landschaft"),
        ("BS", "Basel-Stadt"),
        ("FR", "Freiburg"),
        ("GE", "Genf"),
        ("GL", "Glarus"),
        ("GR", "Graubünden"),
        ("JU", "Jura"),
        ("LU", "Luzern"),
        ("NE", "Neuenburg"),
        ("NW", "Nidwalden"),
        ("OW", "Obwalden"),
        ("SG", "St. Gallen"),
        ("SH", "Schaffhausen"),
        ("SO", "Solothurn"),
        ("SZ", "Schwyz"),
        ("TG", "Thurgau"),
        ("TI", "Tessin"),
        ("UR", "Uri"),
        ("VD", "Waadt"),
        ("VS", "Wallis"),
        ("ZG", "Zug"),
        ("ZH", "Zürich"),
    )

    def canton(self) -> Tuple[str, str]:
        """
        Randomly returns a swiss canton ('Abbreviated', 'Name').
        :example ('ZH', 'Zürich')
        """
        return self.random_element(self.cantons)

    def city_name(self) -> str:
        """
        Randomly returns a swiss city.
        :example 'Zug'
        """
        return self.random_element(self.cities)

    def administrative_unit(self) -> str:
        """
        Randomly returns a Swiss canton name.
        :example 'Zürich'
        """
        return self.canton()[1]

    canton_name = administrative_unit

    def canton_code(self) -> str:
        """
        Randomly returns a Swiss canton code.
        :example 'ZH'
        """
        return self.canton()[0]
