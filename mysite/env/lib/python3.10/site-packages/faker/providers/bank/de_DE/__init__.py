from .. import Provider as BankProvider


class Provider(BankProvider):
    """Implement bank provider for ``de_DE`` locale.

    Source for rules for swift location codes:

    - https://www.ebics.de/de/datenformate
    """

    bban_format = "##################"
    country_code = "DE"

    first_place = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" + "23456789"
    second_place = "ABCDEFGHIJKLMNPQRSTUVWXYZ" + "0123456789"
    swift_location_codes = []
    for i in first_place:
        for j in second_place:
            swift_location_codes.append(str(i) + str(j))
    swift_location_codes = tuple(swift_location_codes)
