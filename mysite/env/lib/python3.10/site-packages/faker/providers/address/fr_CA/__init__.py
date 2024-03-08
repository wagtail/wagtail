from typing import Any

from ..en_CA import Provider as EnCaProvider


class Provider(EnCaProvider):
    #  Most of the parts are identical to en_CA, we simply override those who are not shared between the two.

    city_prefixes = (
        "Ville",
        "Baie",
        "Saint-",
        "Sainte-",
        "Mont-",
        "La",
        "Lac-",
        "L'",
        "L'Île-",
    )

    city_suffixes = (
        "Est",
        "Ouest",
        "-sur-Mer",
    )

    street_prefixes = (
        "rue",
        "rue",
        "chemin",
        "avenue",
        "boulevard",
        "route",
        "rang",
        "allé",
        "montée",
    )

    provinces = (
        "Alberta",
        "Colombie-Britannique",
        "Manitoba",
        "Nouveau-Brunswick",
        "Terre-Neuve-et-Labrador",
        "Territoires du Nord-Ouest",
        "Nouvelle-Écosse",
        "Nunavut",
        "Ontario",
        "Île-du-Prince-Édouard",
        "Québec",
        "Saskatchewan",
        "Yukon",
    )

    street_name_formats = (
        "{{street_prefix}} {{first_name}}",
        "{{street_prefix}} {{last_name}}",
    )

    city_formats = (
        "{{city_prefix}} {{last_name}}",
        "{{city_prefix}} {{last_name}}",
        "{{city_prefix}}-{{city_prefix}}-{{last_name}}",
        "{{city_prefix}} {{first_name}} {{city_suffix}}",
        "{{city_prefix}} {{first_name}}",
        "{{city_prefix}} {{first_name}}",
        "{{city_prefix}} {{first_name}}",
        "{{last_name}}",
        "{{last_name}}",
        "{{first_name}} {{city_suffix}}",
        "{{last_name}} {{city_suffix}}",
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def street_prefix(self) -> str:
        """
        :example: 'rue'
        """
        return self.random_element(self.street_prefixes)
