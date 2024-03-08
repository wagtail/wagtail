from typing import List, Optional, Tuple

from .. import Provider as BankProvider


def get_clabe_control_digit(clabe: str) -> int:
    """Generate the checksum digit for a CLABE.

    :param clabe: CLABE.
    :return: The CLABE checksum digit.
    """
    factors = [3, 7, 1]
    products: List[int] = []

    for i, digit in enumerate(clabe[:17]):
        products.append((int(digit) * factors[i % 3]) % 10)

    return (10 - sum(products)) % 10


def is_valid_clabe(clabe: str) -> bool:
    """Check if a CLABE is valid using the checksum.

    :param clabe: CLABE.
    :return: True if the CLABE is valid, False otherwise.
    """
    if len(clabe) != 18 or not clabe.isdigit():
        return False

    return get_clabe_control_digit(clabe) == int(clabe[-1])


class Provider(BankProvider):
    """Bank provider for ``es_MX`` locale."""

    banks: Tuple[str, ...] = (
        "ABC Capital, S.A. I.B.M.",
        "Acciones y Valores Banamex, S.A. de C.V., Casa de Bolsa",
        "Actinver Casa de Bolsa, S.A. de C.V.",
        "Akala, S.A. de C.V., Sociedad Financiera Popular",
        "American Express Bank (México), S.A.",
        "AXA Seguros, S.A. De C.V.",
        "B y B Casa de Cambio, S.A. de C.V.",
        "Banca Afirme, S.A.",
        "Banca Mifel, S.A.",
        "Banco Actinver, S.A.",
        "Banco Ahorro Famsa, S.A.",
        "Banco Autofin México, S.A.",
        "Banco Azteca, S.A.",
        "Banco BASE, S.A. de I.B.M.",
        "Banco Compartamos, S.A.",
        "Banco Credit Suisse (México), S.A.",
        "Banco del Ahorro Nacional y Servicios Financieros, S.N.C.",
        "Banco del Bajío, S.A.",
        "Banco Inbursa, S.A.",
        "Banco Inmobiliario Mexicano, S.A., Institución de Banca Múltiple",
        "Banco Interacciones, S.A.",
        "Banco Invex, S.A.",
        "Banco J.P. Morgan, S.A.",
        "Banco Mercantil del Norte, S.A.",
        "Banco Monex, S.A.",
        "Banco Multiva, S.A.",
        "Banco Nacional de Comercio Exterior",
        "Banco Nacional de México, S.A.",
        "Banco Nacional de Obras y Servicios Públicos",
        "Banco Nacional del Ejército, Fuerza Aérea y Armada",
        "Banco PagaTodo S.A., Institución de Banca Múltiple",
        "Banco Regional de Monterrey, S.A.",
        "Banco Sabadell, S.A. I.B.M.",
        "Banco Santander, S.A.",
        "Banco Ve por Mas, S.A.",
        "Banco Wal Mart de México Adelante, S.A.",
        "BanCoppel, S.A.",
        "Bank of America México, S.A.",
        "Bank of Tokyo-Mitsubishi UFJ (México), S.A.",
        "Bankaool, S.A., Institución de Banca Múltiple",
        "Bansi, S.A.",
        "Barclays Bank México, S.A.",
        "BBVA Bancomer, S.A.",
        "Bulltick Casa de Bolsa, S.A. de C.V.",
        "Caja Popular Mexicana, S.C. de A.P. de R.L. De C.V.",
        "Casa de Bolsa Finamex, S.A. de C.V.",
        "Casa de Cambio Tíber, S.A. de C.V.",
        "CI Casa de Bolsa, S.A. de C.V.",
        "CLS Bank International",
        "Consubanco, S.A.",
        "Consultoría Internacional Banco, S.A.",
        "Consultoría Internacional Casa de Cambio, S.A. de C.V.",
        "Deutsche Bank México, S.A.",
        "Deutsche Securities, S.A. de C.V.",
        "Estructuradores del Mercado de Valores Casa de Bolsa, S.A. de C.V.",
        "Evercore Casa de Bolsa, S.A. de C.V.",
        "Financiera Nacional De Desarrollo Agropecuario, Rural, F y P.",
        "Fincomún, Servicios Financieros Comunitarios, S.A. de C.V.",
        "GBM Grupo Bursátil Mexicano, S.A. de C.V.",
        "GE Money Bank, S.A.",
        "HDI Seguros, S.A. de C.V.",
        "Hipotecaria su Casita, S.A. de C.V.",
        "HSBC México, S.A.",
        "Industrial and Commercial Bank of China, S.A., Institución de Banca Múltiple",
        "ING Bank (México), S.A.",
        "Inter Banco, S.A.",
        "Intercam Casa de Bolsa, S.A. de C.V.",
        "Intercam Casa de Cambio, S.A. de C.V.",
        "Inversora Bursátil, S.A. de C.V.",
        "IXE Banco, S.A.",
        "J.P. Morgan Casa de Bolsa, S.A. de C.V.",
        "J.P. SOFIEXPRESS, S.A. de C.V., S.F.P.",
        "Kuspit Casa de Bolsa, S.A. de C.V.",
        "Libertad Servicios Financieros, S.A. De C.V.",
        "MAPFRE Tepeyac S.A.",
        "Masari Casa de Bolsa, S.A.",
        "Merrill Lynch México, S.A. de C.V., Casa de Bolsa",
        "Monex Casa de Bolsa, S.A. de C.V.",
        "Multivalores Casa de Bolsa, S.A. de C.V. Multiva Gpo. Fin.",
        "Nacional Financiera, S.N.C.",
        "Opciones Empresariales Del Noreste, S.A. DE C.V.",
        "OPERADORA ACTINVER, S.A. DE C.V.",
        "Operadora De Pagos Móviles De México, S.A. De C.V.",
        "Operadora de Recursos Reforma, S.A. de C.V.",
        "OrderExpress Casa de Cambio , S.A. de C.V. AAC",
        "Profuturo G.N.P., S.A. de C.V.",
        "Scotiabank Inverlat, S.A.",
        "SD. INDEVAL, S.A. de C.V.",
        "Seguros Monterrey New York Life, S.A de C.V.",
        "Sistema de Transferencias y Pagos STP, S.A. de C.V., SOFOM E.N.R.",
        "Skandia Operadora S.A. de C.V.",
        "Skandia Vida S.A. de C.V.",
        "Sociedad Hipotecaria Federal, S.N.C.",
        "Solución Asea, S.A. de C.V., Sociedad Financiera Popular",
        "Sterling Casa de Cambio, S.A. de C.V.",
        "Telecomunicaciones de México",
        "The Royal Bank of Scotland México, S.A.",
        "UBS Banco, S.A.",
        "UNAGRA, S.A. de C.V., S.F.P.",
        "Única Casa de Cambio, S.A. de C.V.",
        "Valores Mexicanos Casa de Bolsa, S.A. de C.V.",
        "Valué, S.A. de C.V., Casa de Bolsa",
        "Vector Casa de Bolsa, S.A. de C.V.",
        "Volkswagen Bank S.A. Institución de Banca Múltiple",
        "Zúrich Compañía de Seguros, S.A.",
        "Zúrich Vida, Compañía de Seguros, S.A.",
    )

    bank_codes: Tuple[int, ...] = (
        2,
        6,
        9,
        12,
        14,
        19,
        21,
        22,
        30,
        32,
        36,
        37,
        42,
        44,
        58,
        59,
        60,
        62,
        72,
        102,
        103,
        106,
        108,
        110,
        112,
        113,
        116,
        124,
        126,
        127,
        128,
        129,
        130,
        131,
        132,
        133,
        134,
        135,
        136,
        137,
        138,
        139,
        140,
        141,
        143,
        145,
        147,
        148,
        150,
        155,
        156,
        166,
        168,
        600,
        601,
        602,
        604,
        605,
        606,
        607,
        608,
        610,
        611,
        613,
        614,
        615,
        616,
        617,
        618,
        619,
        620,
        621,
        622,
        623,
        624,
        626,
        627,
        628,
        629,
        630,
        631,
        632,
        633,
        634,
        636,
        637,
        638,
        640,
        642,
        646,
        647,
        648,
        649,
        651,
        652,
        653,
        655,
        656,
        659,
        670,
        674,
        677,
        679,
        684,
        901,
        902,
    )

    def bank(self) -> str:
        """Generate a mexican bank name.

        :return: A mexican bank name.

        :sample:
        """
        return self.random_element(self.banks)

    def clabe(self, bank_code: Optional[int] = None) -> str:
        """Generate a mexican bank account CLABE.

        Sources:

        - https://en.wikipedia.org/wiki/CLABE

        :return: A fake CLABE number.

        :sample:
        :sample: bank_code=2
        """
        bank = bank_code or self.random_element(self.bank_codes)
        city = self.random_int(0, 999)
        branch = self.random_int(0, 9999)
        account = self.random_int(0, 9999999)

        result = f"{bank:03d}{city:03d}{branch:04d}{account:07d}"
        control_digit = get_clabe_control_digit(result)

        return result + str(control_digit)
