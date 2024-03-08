from .. import BaseProvider, ElementsType, date_time

localized = True


class Provider(BaseProvider):
    city_suffixes: ElementsType[str] = ["Ville"]
    street_suffixes: ElementsType[str] = ["Street"]
    city_formats: ElementsType[str] = ("{{first_name}} {{city_suffix}}",)
    street_name_formats: ElementsType[str] = ("{{last_name}} {{street_suffix}}",)
    street_address_formats: ElementsType[str] = ("{{building_number}} {{street_name}}",)
    address_formats: ElementsType[str] = ("{{street_address}} {{postcode}} {{city}}",)
    building_number_formats: ElementsType[str] = ("##",)
    postcode_formats: ElementsType[str] = ("#####",)
    countries: ElementsType[str] = [country.name for country in date_time.Provider.countries]

    ALPHA_2 = "alpha-2"
    ALPHA_3 = "alpha-3"

    alpha_2_country_codes: ElementsType[str] = [country.alpha_2_code for country in date_time.Provider.countries]
    alpha_3_country_codes: ElementsType[str] = [country.alpha_3_code for country in date_time.Provider.countries]

    def city_suffix(self) -> str:
        """
        :example: 'town'
        """
        return self.random_element(self.city_suffixes)

    def street_suffix(self) -> str:
        """
        :example: 'Avenue'
        """
        return self.random_element(self.street_suffixes)

    def building_number(self) -> str:
        """
        :example: '791'
        """
        return self.numerify(self.random_element(self.building_number_formats))

    def city(self) -> str:
        """
        :example: 'Sashabury'
        """
        pattern: str = self.random_element(self.city_formats)
        return self.generator.parse(pattern)

    def street_name(self) -> str:
        """
        :example: 'Crist Parks'
        """
        pattern: str = self.random_element(self.street_name_formats)
        return self.generator.parse(pattern)

    def street_address(self) -> str:
        """
        :example: '791 Crist Parks'
        """
        pattern: str = self.random_element(self.street_address_formats)
        return self.generator.parse(pattern)

    def postcode(self) -> str:
        """
        :example: 86039-9874
        """
        return self.bothify(self.random_element(self.postcode_formats)).upper()

    def address(self) -> str:
        """
        :example: '791 Crist Parks, Sashabury, IL 86039-9874'
        """
        pattern: str = self.random_element(self.address_formats)
        return self.generator.parse(pattern)

    def country(self) -> str:
        return self.random_element(self.countries)

    def country_code(self, representation: str = ALPHA_2) -> str:
        if representation == self.ALPHA_2:
            return self.random_element(self.alpha_2_country_codes)
        elif representation == self.ALPHA_3:
            return self.random_element(self.alpha_3_country_codes)
        else:
            raise ValueError("`representation` must be one of `alpha-2` or `alpha-3`.")

    def current_country_code(self) -> str:
        try:
            return self.__lang__.split("_")[1]  # type: ignore
        except IndexError:
            raise AttributeError("Country code cannot be determined from locale")

    def current_country(self) -> str:
        current_country_code = self.current_country_code()
        current_country = [
            country.name for country in date_time.Provider.countries if country.alpha_2_code == current_country_code
        ]
        if len(current_country) == 1:
            return current_country[0]  # type: ignore
        elif len(current_country) > 1:
            raise ValueError(f"Ambiguous country for country code {current_country_code}: {current_country}")
        else:
            raise ValueError(f"No appropriate country for country code {current_country_code}")
