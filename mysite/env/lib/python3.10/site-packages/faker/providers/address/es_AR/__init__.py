from collections import OrderedDict
from typing import List, Tuple

from ..es import Provider as AddressProvider


class Provider(AddressProvider):
    provinces = {
        "CABA": "Ciudad Autónoma de Buenos Aires",
        "BA": "Buenos Aires",
        "CA": "Catamarca",
        "CH": "Chaco",
        "CT": "Chubut",
        "CB": "Córdoba",
        "CR": "Corrientes",
        "ER": "Entre Ríos",
        "FO": "Formosa",
        "JY": "Jujuy",
        "LP": "La Pampa",
        "LR": "La Rioja",
        "MZ": "Mendoza",
        "MI": "Misiones",
        "NQN": "Neuquén",
        "RN": "Río Negro",
        "SA": "Salta",
        "SJ": "San Juan",
        "SL": "San Luis",
        "SC": "Santa Cruz",
        "SF": "Santa Fe",
        "SE": "Santiago del Estero",
        "TF": "Tierra del Fuego",
        "TU": "Tucumán",
    }

    municipalities: List[Tuple[str, str, str]] = [
        ("1004", "Constitución", "CABA"),
        ("1900", "La Plata", "BA"),
        ("7600", "Mar del Plata", "BA"),
        ("8000", "Bahía Blanca", "BA"),
        ("4700", "San Ferando del Valle de Catamarca", "CA"),
        ("3500", "Resistencia", "CH"),
        ("9103", "Rawson", "CT"),
        ("9000", "Comodoro Rivadavia", "CT"),
        ("5000", "Córdoba", "CB"),
        ("3400", "Corrientes", "CR"),
        ("3100", "Paraná", "ER"),
        ("3600", "Formosa", "FO"),
        ("4600", "San Salvador de Jujuy", "JY"),
        ("6300", "Santa Rosa", "LP"),
        ("5300", "La Rioja", "LR"),
        ("5360", "Chilecito", "LR"),
        ("5500", "Mendoza", "MZ"),
        ("3300", "Posadas", "MI"),
        ("8300", "Neuquén", "NQN"),
        ("8500", "Viedma", "RN"),
        ("4400", "Salta", "SA"),
        ("5400", "San Juan", "SJ"),
        ("5700", "San Luis", "SL"),
        ("5881", "Merlo", "SL"),
        ("9400", "Río Gallegos", "SC"),
        ("3000", "Santa Fe", "SF"),
        ("2000", "Rosario", "SF"),
        ("4200", "Santiago del Estero", "SE"),
        ("9410", "Ushuaia", "TF"),
        ("4000", "San Miguel de Tucumán", "TU"),
    ]

    street_prefixes = OrderedDict(
        [
            ("Calle", 0.2),
            ("Avenida", 0.2),
            ("Av.", 0.2),
            ("Diagonal", 0.2),
            ("Diag.", 0.05),
            ("Camino", 0.05),
            ("Boulevard", 0.05),
            ("Blv.", 0.05),
        ]
    )
    street_suffixes = ["A", "B", "Bis"]

    street_proceres = (
        "San Martin",
        "Belgrano",
        "Saavedra",
        "Rivadavia",
        "Güemes",
        "G. Brown",
        "J.B. Alberdi",
        "J.M. de Rosas",
        "J.J. Castelli",
        "Mitre",
        "Alem",
        "Alvear",
        "Malvinas Argentinas",
        "Pte. Perón",
        "Omar Nuñez",
    )
    street_name_formats = OrderedDict(
        [
            ("{{street_prefix}} %", 0.2),
            ("{{street_prefix}} {{street_municipality}}", 0.2),
            ("{{street_prefix}} {{street_province}}", 0.2),
            ("{{street_prefix}} {{street_procer}}", 0.2),
            ("{{street_prefix}} 1## {{street_suffix}}", 0.02),
        ]
    )
    building_number_formats = OrderedDict(
        [
            ("%%", 0.2),
            ("%%#", 0.2),
            ("%#%", 0.2),
            ("%#%#", 0.2),
        ]
    )
    secondary_address_formats = [
        "Piso % Dto. %",
        "Dto. %",
        "Torre % Dto. %",
        "Local %!",
        "Oficina %!",
    ]
    postcode_formats = ["{{municipality_code}}####"]

    def provinces_code(self) -> str:
        """
        :example: "BA"
        """
        return self.random_element(self.provinces.keys())

    def province(self) -> str:
        """
        :example: "Buenos Aires"
        """
        return self.random_element(list(self.provinces.values()))

    administrative_unit = province

    def municipality_code(self) -> str:
        """
        :example: "1900"
        """
        return self.random_element(self.municipalities)[0]  # type: ignore

    def municipality(self) -> str:
        """
        :example: "La Plata"
        """
        return self.random_element(self.municipalities)[1]  # type: ignore

    city = municipality

    def street_prefix(self) -> str:
        """
        :example: "Calle"
        """
        return self.random_element(self.street_prefixes)

    def street_procer(self) -> str:
        """
        :example: "Belgrano"
        """
        return self.random_element(self.street_proceres)

    def street_municipality(self) -> str:
        """
        :example: "La Plata"
        """
        return self.random_element(self.municipalities)[1]

    def street_province(self) -> str:
        """
        :example: "San Juan"
        """
        return self.random_element(list(self.provinces.values()))

    def street_suffix(self) -> str:
        """
        :example: "Sur"
        """
        return self.generator.parse(self.random_element(self.street_suffixes))

    def street_name(self) -> str:
        """
        :example: "Calle 1"
        """
        pattern: str = self.random_element(self.street_name_formats)
        return self.numerify(self.generator.parse(pattern))

    def building_number(self) -> str:
        """
        :example: "23"
        """
        return self.numerify(self.generator.parse(self.random_element(self.building_number_formats)))

    def secondary_address(self) -> str:
        """
        :example: "Departamento 123"
        """
        return self.numerify(self.random_element(self.secondary_address_formats))

    def street_address(self) -> str:
        """
        :example: "Calle 1 N° 23"
        """
        return self.street_name() + " N° " + self.building_number()

    def postcode(self) -> str:
        """
        :example: "1900"
        """
        return self.numerify(self.generator.parse(self.random_element(self.postcode_formats)))

    def address(self) -> str:
        """
        :example: "Calle 1 N° 23, La Plata 1900, Buenos Aires"
        """
        municipality: Tuple[str, str, str] = self.random_element(self.municipalities)
        municipality_code = municipality[0]
        municipality_prov = municipality[2]

        secondary_address: str = self.random_element(
            [
                " " + self.secondary_address(),
                "",
            ]
        )
        postcode = "\n" + municipality[1] + " " + municipality_code
        province_name = ", " + self.provinces[municipality_prov]

        return self.street_address() + secondary_address + postcode + province_name
