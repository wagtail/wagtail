from collections import OrderedDict
from typing import Optional

from faker.providers.person.ru_RU import translit

from .. import CardType, CreditCard
from .. import Provider as CreditCardProvider


class Provider(CreditCardProvider):
    """Implement credit card provider for ``ru_RU`` locale.

    For all methods that take ``card_type`` as an argument, a random card type
    will be used if the supplied value is ``None``. The list of valid card types
    includes ``'amex'``, ``'maestro'``, ``'mastercard'``, ``'mir'``,
    ``'unionpay'``, and ``'visa'``.

    Sources:

    - https://en.wikipedia.org/wiki/Payment_card_number#Issuer_identification_number_(IIN)
    """

    prefix_visa = ["4"]
    prefix_mastercard = [
        "51",
        "52",
        "53",
        "54",
        "55",
        "222%",
        "223",
        "224",
        "225",
        "226",
        "227",
        "228",
        "229",
        "23",
        "24",
        "25",
        "26",
        "270",
        "271",
        "2720",
    ]
    prefix_mir = ["2200", "2201", "2202", "2203", "2204"]
    prefix_maestro = [
        "50",
        "56",
        "57",
        "58",
        "59",
        "60",
        "61",
        "62",
        "63",
        "64",
        "65",
        "66",
        "67",
        "68",
        "69",
    ]
    prefix_amex = ["34", "37"]
    prefix_unionpay = ["62", "81"]

    credit_card_types = OrderedDict(
        (
            ("visa", CreditCard("Visa", prefix_visa, security_code="CVV2")),
            (
                "mastercard",
                CreditCard("Mastercard", prefix_mastercard, security_code="CVC2"),
            ),
            ("mir", CreditCard("МИР", prefix_mir)),
            ("maestro", CreditCard("Maestro", prefix_maestro, security_code="CVV2")),
            (
                "amex",
                CreditCard(
                    "American Express",
                    prefix_amex,
                    15,
                    security_code="CID",
                    security_code_length=4,
                ),
            ),
            ("unionpay", CreditCard("Union Pay", prefix_unionpay)),
        )
    )

    def credit_card_full(self, card_type: Optional[CardType] = None) -> str:
        """Generate a set of credit card details."""
        card = self._credit_card_type(card_type)

        tpl = "{provider}\n" "{owner}\n" "{number} {expire_date}\n" "{security}: {security_nb}\n" "{issuer}"

        tpl = tpl.format(
            provider=card.name,
            owner=translit(
                self.generator.parse(
                    self.random_element(
                        [
                            "{{first_name_male}} {{last_name_male}}",
                            "{{first_name_female}} {{last_name_female}}",
                        ]
                    )
                )
            ),
            number=self.credit_card_number(card),
            expire_date=self.credit_card_expire(),
            security=card.security_code,
            security_nb=self.credit_card_security_code(card),
            issuer=self.generator.parse("{{bank}}"),
        )

        return self.generator.parse(tpl)
