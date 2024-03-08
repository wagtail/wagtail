from collections import OrderedDict
from typing import Sequence

from ..en_PH import Provider as EnPhProvider


class Provider(EnPhProvider):
    """
    Provider for company names for fil_PH locale

    Companies in the Philippines rarely have Filipino names, and when they do, the English name is usually used way more
    frequently by the locals. In some cases, the Filipino names are more like in Taglish, so for the purposes of this
    provider, only English company names will be generated for this locale.

    Company and brand taglines in pure Filipino, however, are much more common, so this provider will generate catch
    phrases in pure Filipino randomly alongside the English ones.
    """

    catch_phrase_formats = OrderedDict(
        [
            ("{{english_catch_phrase}}", 0.64),
            (
                "Ang {{random_noun_ish_good_trait}} ng {{random_object_of_concern}}!",
                0.12,
            ),
            (
                "Serbisyong {{random_good_service_adjective}} para sa {{random_object_of_concern}}!",
                0.12,
            ),
            ("Kahit kailan, {{random_good_service_adjective_chain}}!", 0.12),
        ]
    )
    noun_ish_good_traits = (
        "bida",
        "ginhawa",
        "haligi",
        "karangalan",
        "lingkod",
        "liwanag",
        "numero uno",
        "pag-asa",
        "tulay",
    )
    good_service_adjectives = (
        "bida",
        "dekalidad",
        "hindi umaatras",
        "kakaiba",
        "maasahan",
        "magaling",
        "mapatitiwalaan",
        "numero uno",
        "panalo",
        "tagumpay",
        "tama",
        "tapat",
        "totoo",
        "tunay",
        "walang kapantay",
        "walang katulad",
        "walang tatalo",
    )
    objects_of_concern = [
        "Filipino",
        "Pilipinas",
        "Pilipino",
        "Pinoy",
        "bahay",
        "bansa",
        "bayan",
        "buhay",
        "mamamayan",
        "mundo",
        "tahanan",
    ]

    def random_noun_ish_good_trait(self) -> str:
        return self.random_element(self.noun_ish_good_traits)

    def random_good_service_adjective(self) -> str:
        return self.random_element(self.good_service_adjectives)

    def random_good_service_adjective_chain(self) -> str:
        adjectives: Sequence[str] = self.random_elements(self.good_service_adjectives, length=2, unique=True)
        return " at ".join(adjectives)

    def random_object_of_concern(self) -> str:
        return self.random_element(self.objects_of_concern)

    def english_catch_phrase(self) -> str:
        return super().catch_phrase()

    def catch_phrase(self) -> str:
        return self.random_element(self.catch_phrase_formats)
