from ..es import Provider as AddressProvider


class Provider(AddressProvider):
    building_number_formats = ("%", "%#", "%#", "%#", "%##")
    street_prefixes = (
        "Plaza",
        "Calle",
        "Avenida",
        "Via",
        "Vial",
        "Rambla",
        "Glorieta",
        "Urbanización",
        "Callejón",
        "Cañada",
        "Alameda",
        "Acceso",
        "C.",
        "Ronda",
        "Pasaje",
        "Cuesta",
        "Pasadizo",
        "Paseo",
        "Camino",
    )
    states = (
        "Álava",
        "Albacete",
        "Alicante",
        "Almería",
        "Asturias",
        "Ávila",
        "Badajoz",
        "Baleares",
        "Barcelona",
        "Burgos",
        "Cáceres",
        "Cádiz",
        "Cantabria",
        "Castellón",
        "Ceuta",
        "Ciudad",
        "Córdoba",
        "Cuenca",
        "Girona",
        "Granada",
        "Guadalajara",
        "Guipúzcoa",
        "Huelva",
        "Huesca",
        "Jaén",
        "La Coruña",
        "La Rioja",
        "Las Palmas",
        "León",
        "Lleida",
        "Lugo",
        "Madrid",
        "Málaga",
        "Melilla",
        "Murcia",
        "Navarra",
        "Ourense",
        "Palencia",
        "Pontevedra",
        "Salamanca",
        "Santa Cruz de Tenerife",
        "Segovia",
        "Sevilla",
        "Soria",
        "Tarragona",
        "Teruel",
        "Toledo",
        "Valencia",
        "Valladolid",
        "Vizcaya",
        "Zamora",
        "Zaragoza",
    )

    # Source:
    # https://administracionelectronica.gob.es/ctt/resources/Soluciones
    # /238/Descargas/Catalogo-de-Comunidades-Autonomas.xlsx
    regions = (
        "Andalucía",
        "Aragón",
        "Principado de Asturias",
        "Illes Balears",
        "Canarias",
        "Cantabria",
        "Castilla y León",
        "Castilla-La Mancha",
        "Cataluña",
        "Comunitat Valenciana",
        "Extremadura",
        "Galicia",
        "Comunidad de Madrid",
        "Región de Murcia",
        "Comunidad Foral de Navarra",
        "País Vasco",
        "La Rioja",
        "Ciudad Autónoma de Ceuta",
        "Ciudad Autónoma de Melilla",
    )

    city_formats = ("{{state_name}}",)

    street_name_formats = (
        "{{street_prefix}} {{first_name}} {{last_name}}",
        "{{street_prefix}} de {{first_name}} {{last_name}}",
    )
    street_address_formats = (
        "{{street_name}} {{building_number}}",
        "{{street_name}} {{building_number}} {{secondary_address}} ",
    )
    address_formats = ("{{street_address}}\n{{city}}, {{postcode}}",)
    secondary_address_formats = ("Apt. ##", "Piso #", "Puerta #")

    def state_name(self) -> str:
        return self.random_element(self.states)

    def street_prefix(self) -> str:
        return self.random_element(self.street_prefixes)

    def secondary_address(self) -> str:
        return self.numerify(self.random_element(self.secondary_address_formats))

    def administrative_unit(self) -> str:
        return self.random_element(self.states)

    state = administrative_unit

    def region(self) -> str:
        return self.random_element(self.regions)

    def postcode(self) -> str:
        return str(self.generator.random.randint(1000, 52100)).zfill(5)

    autonomous_community = region
