import string

from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    """Implement automotive provider for ``sk_SK`` locale.

    Sources:

    - https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_Slovakia
    """

    license_plate_prefix = [
        "BA",
        "BL",
        "BT",  # Bratislava
        "BB",  # Banska Bystrica
        "BJ",  # Bardejov
        "BN",  # Banovce nad Bebravou
        "BR",  # Brezno
        "BS",  # Banska Stiavnica
        "BY",  # Bytca
        "CA",  # Cadca
        "DK",  # Dolny Kubin
        "DS",  # Dunajska Streda
        "DT",  # Detva
        "GA",  # Galanta
        "GL",  # Gelnica
        "HC",  # Hlohovec
        "HE",  # Humenne
        "IL",  # Ilava
        "KA",  # Krupina
        "KE",  # Kosice
        "KK",  # Kezmarok
        "KM",  # Kysucke Nove Mesto
        "KN",  # Komarno
        "KS",  # Kosice-okolie
        "LC",  # Lucenec
        "LE",  # Levoca
        "LM",  # Liptovsky Mikulas
        "LV",  # Levice
        "MA",  # Malacky
        "MI",  # Michalovce
        "ML",  # Medzilaborce
        "MT",  # Martin
        "MY",  # Myjava
        "NR",  # Nitra
        "NM",  # Nove Mesto nad Vahom
        "NO",  # Namestovo
        "NZ",  # Nove Zamky
        "PB",  # Povazska Bystrica
        "PD",  # Prievidza
        "PE",  # Partizanske
        "PK",  # Pezinok
        "PN",  # Piestany
        "PO",  # Presov
        "PP",  # Poprad
        "PT",  # Poltar
        "PU",  # Puchov
        "RA",  # Revuca
        "RK",  # Ruzomberok
        "RS",  # Rimavska Sobota
        "RV",  # Roznava
        "SA",  # Sala
        "SB",  # Sabinov
        "SC",  # Senec
        "SE",  # Senica
        "SI",  # Skalica
        "SK",  # Svidnik
        "SL",  # Stara Lubovna
        "SN",  # Spisska Nova Ves
        "SO",  # Sobrance
        "SP",  # Stropkov
        "SV",  # Snina
        "TT",  # Trnava
        "TN",  # Trencin
        "TO",  # Topolcany
        "TR",  # Turcianske Teplice
        "TS",  # Tvrdosin
        "TV",  # Trebisov
        "VK",  # Velky Krtis
        "VT",  # Vranov nad Toplou
        "ZA",  # Zilina
        "ZC",  # Zarnovica
        "ZH",  # Ziar nad Hronom
        "ZM",  # Zlate Moravce
        "ZV",  # Zvolen
    ]

    license_plate_suffix = ("###??",)

    def license_plate(self) -> str:
        """Generate a license plate."""
        prefix: str = self.random_element(self.license_plate_prefix)
        suffix = self.bothify(
            self.random_element(self.license_plate_suffix),
            letters=string.ascii_uppercase,
        )
        return prefix + suffix
