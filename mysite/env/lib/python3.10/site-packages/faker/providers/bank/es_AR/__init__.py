from .. import Provider as BankProvider


class Provider(BankProvider):
    """Implement bank provider for ``es_AR`` locale.
    source: https://www.bcra.gob.ar/SistemasFinancierosYdePagos/Activos.asp"""

    bban_format = "????####################"
    country_code = "AR"

    banks = (
        "Banco de la Nación Argentina",
        "Banco Santander",
        "Banco de Galicia y Buenos Aires",
        "Banco de la Provincia de Buenos Aires",
        "BBVA Argentina",
        "Banco Macro",
        "HSBC Bank Argentina",
        "Banco Ciudad de Buenos Aires",
        "Banco Credicoop",
        "Industrial And Commercial Bank Of China",
        "Citibank",
        "Banco Patagonia",
        "Banco de la Provincia de Córdoba",
        "Banco Supervielle",
        "Nuevo Banco de Santa Fe",
        "Banco Hipotecario S. A.",
        "Banco Itaú Argentina",
        "Banco de Inversión y Comercio Exterior (BICE)",
        "Banco Comafi",
        "BSE - Banco Santiago del Estero",
    )

    def bank(self) -> str:
        """Generate a bank name."""
        return self.random_element(self.banks)
