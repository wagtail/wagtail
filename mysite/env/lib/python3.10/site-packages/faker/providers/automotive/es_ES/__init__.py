# -*- coding: utf-8 -*-

import re

from typing import Optional

from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    """Implement automotive provider for ``es_ES`` locale.

    Sources:

    - https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_Spain

    .. |license_plate_unified| replace::
       :meth:`license_plate_unified() <faker.providers.automotive.es_ES.Provider.license_plate_unified>`

    .. |license_plate_by_province| replace::
       :meth:`license_plate_by_province() <faker.providers.automotive.es_ES.Provider.license_plate_by_province>`
    """

    license_formats = (
        # New format
        "#### ???",
    )

    # New format suffix letters (excluding vocals and Q from ascii uppercase)
    license_plate_new_format_suffix_letters = "BCDFGHJKLMNPRSTVWXYZ"

    # Old format suffix letters (excluding Q and R from ascii uppercase)
    license_plate_old_format_suffix_letters = "ABCDEFGHIJKLMNOPSTUVWXYZ"

    # Province prefixes (for old format)
    province_prefix = (
        "A",  # Alicante
        "AB",  # Albacete
        "AL",  # Almería
        "AV",  # Ávila
        "B",  # Barcelona
        "BA",  # Badajoz
        "BI",  # Bilbao
        "BU",  # Burgos
        "C",  # La Coruña
        "CA",  # Cádiz
        "CC",  # Cáceres
        "CS",  # Castellón de la Plana
        "CE",  # Ceuta
        "CO",  # Córdoba
        "CR",  # Ciudad Real
        "CU",  # Cuenca
        "GC",  # Las Palmas (Gran Canaria)
        "GE",  # Girona (until 1992)
        "GI",  # Girona (since 1992)
        "GR",  # Granada
        "GU",  # Guadalajara
        "H",  # Huelva
        "HU",  # Huesca
        "PM",  # Palma de Mallorca (until 1997)
        "IB",  # Islas Baleares (since 1997)
        "J",  # Jaén
        "L",  # Lleida
        "LE",  # León
        "LO",  # Logroño
        "LU",  # Lugo
        "M",  # Madrid
        "MA",  # Málaga
        "ML",  # Melilla
        "MU",  # Murcia
        "O",  # Oviedo
        "OR",  # Ourense (until 1998)
        "OU",  # Ourense (since 1998)
        "P",  # Palencia
        "NA",  # Navarra
        "PO",  # Pontevedra
        "S",  # Santander
        "SA",  # Salamanca
        "SE",  # Sevilla
        "SG",  # Segovia
        "SO",  # Soria
        "SS",  # Donostia/San Sebastián
        "T",  # Tarragona
        "TE",  # Teruel
        "TF",  # Santa Cruz de Tenerife
        "TO",  # Toledo
        "V",  # Valencia
        "VA",  # Valladolid
        "VI",  # Vitoria
        "Z",  # Zaragoza
        "ZA",  # Zamora
    )

    def license_plate_unified(self) -> str:
        """Generate a unified license plate."""
        temp = re.sub(
            r"\?",
            lambda x: self.random_element(self.license_plate_new_format_suffix_letters),
            self.license_formats[0],
        )
        return self.numerify(temp)

    def license_plate_by_province(self, province_prefix: Optional[str] = None) -> str:
        """Generate a provincial license plate.

        If a value for ``province_prefix`` is provided, the value will be used
        as the prefix regardless of validity. If ``None``, then a valid prefix
        will be selected at random.
        """
        province_prefix = province_prefix if province_prefix is not None else self.random_element(self.province_prefix)
        temp = re.sub(
            r"\?",
            lambda x: self.random_element(self.license_plate_old_format_suffix_letters),
            "#### ??",
        )
        return province_prefix + " " + self.numerify(temp)

    def license_plate(self) -> str:
        """Generate a license plate.

        This method randomly chooses (50/50) between |license_plate_unified|
        or |license_plate_by_province| to generate the result.
        """
        if self.generator.random.randint(0, 1):
            return self.license_plate_unified()
        return self.license_plate_by_province()
