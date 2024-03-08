import platform
import re

from calendar import timegm
from datetime import MAXYEAR
from datetime import date as dtdate
from datetime import datetime
from datetime import time as dttime
from datetime import timedelta
from datetime import tzinfo as TzInfo
from typing import Any, Callable, Dict, Iterator, Optional, Tuple, Union

from dateutil import relativedelta
from dateutil.tz import gettz, tzlocal, tzutc

from faker.typing import Country, DateParseType

from .. import BaseProvider, ElementsType

localized = True


def datetime_to_timestamp(dt: Union[dtdate, datetime]) -> int:
    if isinstance(dt, datetime) and getattr(dt, "tzinfo", None) is not None:
        dt = dt.astimezone(tzutc())
    return timegm(dt.timetuple())


def timestamp_to_datetime(timestamp: Union[int, float], tzinfo: Optional[TzInfo]) -> datetime:
    if tzinfo is None:
        pick = convert_timestamp_to_datetime(timestamp, tzlocal())
        return pick.astimezone(tzutc()).replace(tzinfo=None)
    return convert_timestamp_to_datetime(timestamp, tzinfo)


def change_year(current_date: dtdate, year_diff: int) -> dtdate:
    """
    Unless the current_date is February 29th, it is fine to just subtract years.
    If it is a leap day, and we are rolling back to a non-leap year, it will
    cause a ValueError.
    Since this is relatively uncommon, just catch the error and roll forward to
    March 1

    current_date: date  object
    year_diff: int year delta value, positive or negative
    """
    year = current_date.year + year_diff
    try:
        return current_date.replace(year=year)
    except ValueError as e:
        # ValueError thrown if trying to move date to a non-leap year if the current
        # date is February 29th
        if year != 0 and current_date.month == 2 and current_date.day == 29:
            return current_date.replace(month=3, day=1, year=year)
        else:
            raise e


class ParseError(ValueError):
    pass


timedelta_pattern: str = r""
for name, sym in [
    ("years", "y"),
    ("months", "M"),
    ("weeks", "w"),
    ("days", "d"),
    ("hours", "h"),
    ("minutes", "m"),
    ("seconds", "s"),
]:
    timedelta_pattern += r"((?P<{}>(?:\+|-)\d+?){})?".format(name, sym)


class Provider(BaseProvider):
    # NOTE: Windows only guarantee second precision, in order to emulate that
    #       we need to inspect the platform to determine which function is most
    #       appropriate to generate random seconds with.
    if platform.system() == "Windows":

        def _rand_seconds(self, start_datetime: int, end_datetime: int) -> float:
            return self.generator.random.randint(start_datetime, end_datetime)

    else:

        def _rand_seconds(self, start_datetime: int, end_datetime: int) -> float:
            if start_datetime > end_datetime:
                raise ValueError("empty range for _rand_seconds: start datetime must be before than end datetime")
            return self.generator.random.uniform(start_datetime, end_datetime)

    centuries: ElementsType[str] = [
        "I",
        "II",
        "III",
        "IV",
        "V",
        "VI",
        "VII",
        "VIII",
        "IX",
        "X",
        "XI",
        "XII",
        "XIII",
        "XIV",
        "XV",
        "XVI",
        "XVII",
        "XVIII",
        "XIX",
        "XX",
        "XXI",
    ]

    countries = [
        Country(
            timezones=["Europe/Andorra"],
            alpha_2_code="AD",
            alpha_3_code="AND",
            continent="Europe",
            name="Andorra",
            capital="Andorra la Vella",
        ),
        Country(
            timezones=["Asia/Kabul"],
            alpha_2_code="AF",
            alpha_3_code="AFG",
            continent="Asia",
            name="Afghanistan",
            capital="Kabul",
        ),
        Country(
            timezones=["America/Antigua"],
            alpha_2_code="AG",
            alpha_3_code="ATG",
            continent="North America",
            name="Antigua and Barbuda",
            capital="St. John's",
        ),
        Country(
            timezones=["Europe/Tirane"],
            alpha_2_code="AL",
            alpha_3_code="ALB",
            continent="Europe",
            name="Albania",
            capital="Tirana",
        ),
        Country(
            timezones=["Asia/Yerevan"],
            alpha_2_code="AM",
            alpha_3_code="ARM",
            continent="Asia",
            name="Armenia",
            capital="Yerevan",
        ),
        Country(
            timezones=["Africa/Luanda"],
            alpha_2_code="AO",
            alpha_3_code="AGO",
            continent="Africa",
            name="Angola",
            capital="Luanda",
        ),
        Country(
            timezones=[
                "America/Argentina/Buenos_Aires",
                "America/Argentina/Cordoba",
                "America/Argentina/Jujuy",
                "America/Argentina/Tucuman",
                "America/Argentina/Catamarca",
                "America/Argentina/La_Rioja",
                "America/Argentina/San_Juan",
                "America/Argentina/Mendoza",
                "America/Argentina/Rio_Gallegos",
                "America/Argentina/Ushuaia",
            ],
            alpha_2_code="AR",
            alpha_3_code="ARG",
            continent="South America",
            name="Argentina",
            capital="Buenos Aires",
        ),
        Country(
            timezones=["Europe/Vienna"],
            alpha_2_code="AT",
            alpha_3_code="AUT",
            continent="Europe",
            name="Austria",
            capital="Vienna",
        ),
        Country(
            timezones=[
                "Australia/Lord_Howe",
                "Australia/Hobart",
                "Australia/Currie",
                "Australia/Melbourne",
                "Australia/Sydney",
                "Australia/Broken_Hill",
                "Australia/Brisbane",
                "Australia/Lindeman",
                "Australia/Adelaide",
                "Australia/Darwin",
                "Australia/Perth",
            ],
            alpha_2_code="AU",
            alpha_3_code="AUS",
            continent="Oceania",
            name="Australia",
            capital="Canberra",
        ),
        Country(
            timezones=["Asia/Baku"],
            alpha_2_code="AZ",
            alpha_3_code="AZE",
            continent="Asia",
            name="Azerbaijan",
            capital="Baku",
        ),
        Country(
            timezones=["America/Barbados"],
            alpha_2_code="BB",
            alpha_3_code="BRB",
            continent="North America",
            name="Barbados",
            capital="Bridgetown",
        ),
        Country(
            timezones=["Asia/Dhaka"],
            alpha_2_code="BD",
            alpha_3_code="BGD",
            continent="Asia",
            name="Bangladesh",
            capital="Dhaka",
        ),
        Country(
            timezones=["Europe/Brussels"],
            alpha_2_code="BE",
            alpha_3_code="BEL",
            continent="Europe",
            name="Belgium",
            capital="Brussels",
        ),
        Country(
            timezones=["Africa/Ouagadougou"],
            alpha_2_code="BF",
            alpha_3_code="BFA",
            continent="Africa",
            name="Burkina Faso",
            capital="Ouagadougou",
        ),
        Country(
            timezones=["Europe/Sofia"],
            alpha_2_code="BG",
            alpha_3_code="BGR",
            continent="Europe",
            name="Bulgaria",
            capital="Sofia",
        ),
        Country(
            timezones=["Asia/Bahrain"],
            alpha_2_code="BH",
            alpha_3_code="BHR",
            continent="Asia",
            name="Bahrain",
            capital="Manama",
        ),
        Country(
            timezones=["Africa/Bujumbura"],
            alpha_2_code="BI",
            alpha_3_code="BDI",
            continent="Africa",
            name="Burundi",
            capital="Bujumbura",
        ),
        Country(
            timezones=["Africa/Porto-Novo"],
            alpha_2_code="BJ",
            alpha_3_code="BEN",
            continent="Africa",
            name="Benin",
            capital="Porto-Novo",
        ),
        Country(
            timezones=["Asia/Brunei"],
            alpha_2_code="BN",
            alpha_3_code="BRN",
            continent="Asia",
            name="Brunei Darussalam",
            capital="Bandar Seri Begawan",
        ),
        Country(
            timezones=["America/La_Paz"],
            alpha_2_code="BO",
            alpha_3_code="BOL",
            continent="South America",
            name="Bolivia",
            capital="Sucre",
        ),
        Country(
            timezones=[
                "America/Noronha",
                "America/Belem",
                "America/Fortaleza",
                "America/Recife",
                "America/Araguaina",
                "America/Maceio",
                "America/Bahia",
                "America/Sao_Paulo",
                "America/Campo_Grande",
                "America/Cuiaba",
                "America/Porto_Velho",
                "America/Boa_Vista",
                "America/Manaus",
                "America/Eirunepe",
                "America/Rio_Branco",
            ],
            alpha_2_code="BR",
            alpha_3_code="BRA",
            continent="South America",
            name="Brazil",
            capital="Bras\xc3\xadlia",
        ),
        Country(
            timezones=["America/Nassau"],
            alpha_2_code="BS",
            alpha_3_code="BHS",
            continent="North America",
            name="Bahamas",
            capital="Nassau",
        ),
        Country(
            timezones=["Asia/Thimphu"],
            alpha_2_code="BT",
            alpha_3_code="BTN",
            continent="Asia",
            name="Bhutan",
            capital="Thimphu",
        ),
        Country(
            timezones=["Africa/Gaborone"],
            alpha_2_code="BW",
            alpha_3_code="BWA",
            continent="Africa",
            name="Botswana",
            capital="Gaborone",
        ),
        Country(
            timezones=["Europe/Minsk"],
            alpha_2_code="BY",
            alpha_3_code="BLR",
            continent="Europe",
            name="Belarus",
            capital="Minsk",
        ),
        Country(
            timezones=["America/Belize"],
            alpha_2_code="BZ",
            alpha_3_code="BLZ",
            continent="North America",
            name="Belize",
            capital="Belmopan",
        ),
        Country(
            timezones=[
                "America/St_Johns",
                "America/Halifax",
                "America/Glace_Bay",
                "America/Moncton",
                "America/Goose_Bay",
                "America/Blanc-Sablon",
                "America/Montreal",
                "America/Toronto",
                "America/Nipigon",
                "America/Thunder_Bay",
                "America/Pangnirtung",
                "America/Iqaluit",
                "America/Atikokan",
                "America/Rankin_Inlet",
                "America/Winnipeg",
                "America/Rainy_River",
                "America/Cambridge_Bay",
                "America/Regina",
                "America/Swift_Current",
                "America/Edmonton",
                "America/Yellowknife",
                "America/Inuvik",
                "America/Dawson_Creek",
                "America/Vancouver",
                "America/Whitehorse",
                "America/Dawson",
            ],
            alpha_2_code="CA",
            alpha_3_code="CAN",
            continent="North America",
            name="Canada",
            capital="Ottawa",
        ),
        Country(
            timezones=["Africa/Kinshasa", "Africa/Lubumbashi"],
            alpha_2_code="CD",
            alpha_3_code="COD",
            continent="Africa",
            name="Democratic Republic of the Congo",
            capital="Kinshasa",
        ),
        Country(
            timezones=["Africa/Brazzaville"],
            alpha_2_code="CG",
            alpha_3_code="COG",
            continent="Africa",
            name="Republic of the Congo",
            capital="Brazzaville",
        ),
        Country(
            timezones=["Africa/Abidjan"],
            alpha_2_code="CI",
            alpha_3_code="CIV",
            continent="Africa",
            name="C\xc3\xb4te d'Ivoire",
            capital="Yamoussoukro",
        ),
        Country(
            timezones=["America/Santiago", "Pacific/Easter"],
            alpha_2_code="CL",
            alpha_3_code="CHL",
            continent="South America",
            name="Chile",
            capital="Santiago",
        ),
        Country(
            timezones=["Africa/Douala"],
            alpha_2_code="CM",
            alpha_3_code="CMR",
            continent="Africa",
            name="Cameroon",
            capital="Yaound\xc3\xa9",
        ),
        Country(
            timezones=[
                "Asia/Shanghai",
                "Asia/Harbin",
                "Asia/Chongqing",
                "Asia/Urumqi",
                "Asia/Kashgar",
            ],
            alpha_2_code="CN",
            alpha_3_code="CHN",
            continent="Asia",
            name="People's Republic of China",
            capital="Beijing",
        ),
        Country(
            timezones=["America/Bogota"],
            alpha_2_code="CO",
            alpha_3_code="COL",
            continent="South America",
            name="Colombia",
            capital="Bogot\xc3\xa1",
        ),
        Country(
            timezones=["America/Costa_Rica"],
            alpha_2_code="CR",
            alpha_3_code="CRI",
            continent="North America",
            name="Costa Rica",
            capital="San Jos\xc3\xa9",
        ),
        Country(
            timezones=["America/Havana"],
            alpha_2_code="CU",
            alpha_3_code="CUB",
            continent="North America",
            name="Cuba",
            capital="Havana",
        ),
        Country(
            timezones=["Atlantic/Cape_Verde"],
            alpha_2_code="CV",
            alpha_3_code="CPV",
            continent="Africa",
            name="Cape Verde",
            capital="Praia",
        ),
        Country(
            timezones=["Asia/Nicosia"],
            alpha_2_code="CY",
            alpha_3_code="CYP",
            continent="Asia",
            name="Cyprus",
            capital="Nicosia",
        ),
        Country(
            timezones=["Europe/Prague"],
            alpha_2_code="CZ",
            alpha_3_code="CZE",
            continent="Europe",
            name="Czech Republic",
            capital="Prague",
        ),
        Country(
            timezones=["Europe/Berlin"],
            alpha_2_code="DE",
            alpha_3_code="DEU",
            continent="Europe",
            name="Germany",
            capital="Berlin",
        ),
        Country(
            timezones=["Africa/Djibouti"],
            alpha_2_code="DJ",
            alpha_3_code="DJI",
            continent="Africa",
            name="Djibouti",
            capital="Djibouti City",
        ),
        Country(
            timezones=["Europe/Copenhagen"],
            alpha_2_code="DK",
            alpha_3_code="DNK",
            continent="Europe",
            name="Denmark",
            capital="Copenhagen",
        ),
        Country(
            timezones=["America/Dominica"],
            alpha_2_code="DM",
            alpha_3_code="DMA",
            continent="North America",
            name="Dominica",
            capital="Roseau",
        ),
        Country(
            timezones=["America/Santo_Domingo"],
            alpha_2_code="DO",
            alpha_3_code="DOM",
            continent="North America",
            name="Dominican Republic",
            capital="Santo Domingo",
        ),
        Country(
            timezones=["America/Guayaquil", "Pacific/Galapagos"],
            alpha_2_code="EC",
            alpha_3_code="ECU",
            continent="South America",
            name="Ecuador",
            capital="Quito",
        ),
        Country(
            timezones=["Europe/Tallinn"],
            alpha_2_code="EE",
            alpha_3_code="EST",
            continent="Europe",
            name="Estonia",
            capital="Tallinn",
        ),
        Country(
            timezones=["Africa/Cairo"],
            alpha_2_code="EG",
            alpha_3_code="EGY",
            continent="Africa",
            name="Egypt",
            capital="Cairo",
        ),
        Country(
            timezones=["Africa/Asmera"],
            alpha_2_code="ER",
            alpha_3_code="ERI",
            continent="Africa",
            name="Eritrea",
            capital="Asmara",
        ),
        Country(
            timezones=["Africa/Addis_Ababa"],
            alpha_2_code="ET",
            alpha_3_code="ETH",
            continent="Africa",
            name="Ethiopia",
            capital="Addis Ababa",
        ),
        Country(
            timezones=["Europe/Helsinki"],
            alpha_2_code="FI",
            alpha_3_code="FIN",
            continent="Europe",
            name="Finland",
            capital="Helsinki",
        ),
        Country(
            timezones=["Pacific/Fiji"],
            alpha_2_code="FJ",
            alpha_3_code="FJI",
            continent="Oceania",
            name="Fiji",
            capital="Suva",
        ),
        Country(
            timezones=["Europe/Paris"],
            alpha_2_code="FR",
            alpha_3_code="FRA",
            continent="Europe",
            name="France",
            capital="Paris",
        ),
        Country(
            timezones=["Africa/Libreville"],
            alpha_2_code="GA",
            alpha_3_code="GAB",
            continent="Africa",
            name="Gabon",
            capital="Libreville",
        ),
        Country(
            timezones=["Asia/Tbilisi"],
            alpha_2_code="GE",
            alpha_3_code="GEO",
            continent="Asia",
            name="Georgia",
            capital="Tbilisi",
        ),
        Country(
            timezones=["Africa/Accra"],
            alpha_2_code="GH",
            alpha_3_code="GHA",
            continent="Africa",
            name="Ghana",
            capital="Accra",
        ),
        Country(
            timezones=["Africa/Banjul"],
            alpha_2_code="GM",
            alpha_3_code="GMB",
            continent="Africa",
            name="The Gambia",
            capital="Banjul",
        ),
        Country(
            timezones=["Africa/Conakry"],
            alpha_2_code="GN",
            alpha_3_code="GIN",
            continent="Africa",
            name="Guinea",
            capital="Conakry",
        ),
        Country(
            timezones=["Europe/Athens"],
            alpha_2_code="GR",
            alpha_3_code="GRC",
            continent="Europe",
            name="Greece",
            capital="Athens",
        ),
        Country(
            timezones=["America/Guatemala"],
            alpha_2_code="GT",
            alpha_3_code="GTM",
            continent="North America",
            name="Guatemala",
            capital="Guatemala City",
        ),
        Country(
            timezones=["America/Guatemala"],
            alpha_2_code="HT",
            alpha_3_code="HTI",
            continent="North America",
            name="Haiti",
            capital="Port-au-Prince",
        ),
        Country(
            timezones=["Africa/Bissau"],
            alpha_2_code="GW",
            alpha_3_code="GNB",
            continent="Africa",
            name="Guinea-Bissau",
            capital="Bissau",
        ),
        Country(
            timezones=["America/Guyana"],
            alpha_2_code="GY",
            alpha_3_code="GUY",
            continent="South America",
            name="Guyana",
            capital="Georgetown",
        ),
        Country(
            timezones=["America/Tegucigalpa"],
            alpha_2_code="HN",
            alpha_3_code="HND",
            continent="North America",
            name="Honduras",
            capital="Tegucigalpa",
        ),
        Country(
            timezones=["Europe/Budapest"],
            alpha_2_code="HU",
            alpha_3_code="HUN",
            continent="Europe",
            name="Hungary",
            capital="Budapest",
        ),
        Country(
            timezones=[
                "Asia/Jakarta",
                "Asia/Pontianak",
                "Asia/Makassar",
                "Asia/Jayapura",
            ],
            alpha_2_code="ID",
            alpha_3_code="IDN",
            continent="Asia",
            name="Indonesia",
            capital="Jakarta",
        ),
        Country(
            timezones=["Europe/Dublin"],
            alpha_2_code="IE",
            alpha_3_code="IRL",
            continent="Europe",
            name="Republic of Ireland",
            capital="Dublin",
        ),
        Country(
            timezones=["Asia/Jerusalem"],
            alpha_2_code="IL",
            alpha_3_code="ISR",
            continent="Asia",
            name="Israel",
            capital="Jerusalem",
        ),
        Country(
            timezones=["Asia/Calcutta"],
            alpha_2_code="IN",
            alpha_3_code="IND",
            continent="Asia",
            name="India",
            capital="New Delhi",
        ),
        Country(
            timezones=["Asia/Baghdad"],
            alpha_2_code="IQ",
            alpha_3_code="IRQ",
            continent="Asia",
            name="Iraq",
            capital="Baghdad",
        ),
        Country(
            timezones=["Asia/Tehran"],
            alpha_2_code="IR",
            alpha_3_code="IRN",
            continent="Asia",
            name="Iran",
            capital="Tehran",
        ),
        Country(
            timezones=["Atlantic/Reykjavik"],
            alpha_2_code="IS",
            alpha_3_code="ISL",
            continent="Europe",
            name="Iceland",
            capital="Reykjav\xc3\xadk",
        ),
        Country(
            timezones=["Europe/Rome"],
            alpha_2_code="IT",
            alpha_3_code="ITA",
            continent="Europe",
            name="Italy",
            capital="Rome",
        ),
        Country(
            timezones=["America/Jamaica"],
            alpha_2_code="JM",
            alpha_3_code="JAM",
            continent="North America",
            name="Jamaica",
            capital="Kingston",
        ),
        Country(
            timezones=["Asia/Amman"],
            alpha_2_code="JO",
            alpha_3_code="JOR",
            continent="Asia",
            name="Jordan",
            capital="Amman",
        ),
        Country(
            timezones=["Asia/Tokyo"],
            alpha_2_code="JP",
            alpha_3_code="JPN",
            continent="Asia",
            name="Japan",
            capital="Tokyo",
        ),
        Country(
            timezones=["Africa/Nairobi"],
            alpha_2_code="KE",
            alpha_3_code="KEN",
            continent="Africa",
            name="Kenya",
            capital="Nairobi",
        ),
        Country(
            timezones=["Asia/Bishkek"],
            alpha_2_code="KG",
            alpha_3_code="KGZ",
            continent="Asia",
            name="Kyrgyzstan",
            capital="Bishkek",
        ),
        Country(
            timezones=["Pacific/Tarawa", "Pacific/Enderbury", "Pacific/Kiritimati"],
            alpha_2_code="KI",
            alpha_3_code="KIR",
            continent="Oceania",
            name="Kiribati",
            capital="Tarawa",
        ),
        Country(
            timezones=["Asia/Pyongyang"],
            alpha_2_code="KP",
            alpha_3_code="PRK",
            continent="Asia",
            name="North Korea",
            capital="Pyongyang",
        ),
        Country(
            timezones=["Asia/Seoul"],
            alpha_2_code="KR",
            alpha_3_code="KOR",
            continent="Asia",
            name="South Korea",
            capital="Seoul",
        ),
        Country(
            timezones=["Asia/Kuwait"],
            alpha_2_code="KW",
            alpha_3_code="KWT",
            continent="Asia",
            name="Kuwait",
            capital="Kuwait City",
        ),
        Country(
            timezones=["Asia/Beirut"],
            alpha_2_code="LB",
            alpha_3_code="LBN",
            continent="Asia",
            name="Lebanon",
            capital="Beirut",
        ),
        Country(
            timezones=["Europe/Vaduz"],
            alpha_2_code="LI",
            alpha_3_code="LIE",
            continent="Europe",
            name="Liechtenstein",
            capital="Vaduz",
        ),
        Country(
            timezones=["Africa/Monrovia"],
            alpha_2_code="LR",
            alpha_3_code="LBR",
            continent="Africa",
            name="Liberia",
            capital="Monrovia",
        ),
        Country(
            timezones=["Africa/Maseru"],
            alpha_2_code="LS",
            alpha_3_code="LSO",
            continent="Africa",
            name="Lesotho",
            capital="Maseru",
        ),
        Country(
            timezones=["Europe/Vilnius"],
            alpha_2_code="LT",
            alpha_3_code="LTU",
            continent="Europe",
            name="Lithuania",
            capital="Vilnius",
        ),
        Country(
            timezones=["Europe/Luxembourg"],
            alpha_2_code="LU",
            alpha_3_code="LUX",
            continent="Europe",
            name="Luxembourg",
            capital="Luxembourg City",
        ),
        Country(
            timezones=["Europe/Riga"],
            alpha_2_code="LV",
            alpha_3_code="LVA",
            continent="Europe",
            name="Latvia",
            capital="Riga",
        ),
        Country(
            timezones=["Africa/Tripoli"],
            alpha_2_code="LY",
            alpha_3_code="LBY",
            continent="Africa",
            name="Libya",
            capital="Tripoli",
        ),
        Country(
            timezones=["Indian/Antananarivo"],
            alpha_2_code="MG",
            alpha_3_code="MDG",
            continent="Africa",
            name="Madagascar",
            capital="Antananarivo",
        ),
        Country(
            timezones=["Pacific/Majuro", "Pacific/Kwajalein"],
            alpha_2_code="MH",
            alpha_3_code="MHL",
            continent="Oceania",
            name="Marshall Islands",
            capital="Majuro",
        ),
        Country(
            timezones=["Europe/Skopje"],
            alpha_2_code="MK",
            alpha_3_code="MKD",
            continent="Europe",
            name="North Macedonia",
            capital="Skopje",
        ),
        Country(
            timezones=["Africa/Bamako"],
            alpha_2_code="ML",
            alpha_3_code="MLI",
            continent="Africa",
            name="Mali",
            capital="Bamako",
        ),
        Country(
            timezones=["Asia/Rangoon"],
            alpha_2_code="MM",
            alpha_3_code="MMR",
            continent="Asia",
            name="Myanmar",
            capital="Naypyidaw",
        ),
        Country(
            timezones=["Asia/Ulaanbaatar", "Asia/Hovd", "Asia/Choibalsan"],
            alpha_2_code="MN",
            alpha_3_code="MNG",
            continent="Asia",
            name="Mongolia",
            capital="Ulaanbaatar",
        ),
        Country(
            timezones=["Africa/Nouakchott"],
            alpha_2_code="MR",
            alpha_3_code="MRT",
            continent="Africa",
            name="Mauritania",
            capital="Nouakchott",
        ),
        Country(
            timezones=["Europe/Malta"],
            alpha_2_code="MT",
            alpha_3_code="MLT",
            continent="Europe",
            name="Malta",
            capital="Valletta",
        ),
        Country(
            timezones=["Indian/Mauritius"],
            alpha_2_code="MU",
            alpha_3_code="MUS",
            continent="Africa",
            name="Mauritius",
            capital="Port Louis",
        ),
        Country(
            timezones=["Indian/Maldives"],
            alpha_2_code="MV",
            alpha_3_code="MDV",
            continent="Asia",
            name="Maldives",
            capital="Mal\xc3\xa9",
        ),
        Country(
            timezones=["Africa/Blantyre"],
            alpha_2_code="MW",
            alpha_3_code="MWI",
            continent="Africa",
            name="Malawi",
            capital="Lilongwe",
        ),
        Country(
            timezones=[
                "America/Mexico_City",
                "America/Cancun",
                "America/Merida",
                "America/Monterrey",
                "America/Mazatlan",
                "America/Chihuahua",
                "America/Hermosillo",
                "America/Tijuana",
            ],
            alpha_2_code="MX",
            alpha_3_code="MEX",
            continent="North America",
            name="Mexico",
            capital="Mexico City",
        ),
        Country(
            timezones=["Asia/Kuala_Lumpur", "Asia/Kuching"],
            alpha_2_code="MY",
            alpha_3_code="MYS",
            continent="Asia",
            name="Malaysia",
            capital="Kuala Lumpur",
        ),
        Country(
            timezones=["Africa/Maputo"],
            alpha_2_code="MZ",
            alpha_3_code="MOZ",
            continent="Africa",
            name="Mozambique",
            capital="Maputo",
        ),
        Country(
            timezones=["Africa/Windhoek"],
            alpha_2_code="NA",
            alpha_3_code="NAM",
            continent="Africa",
            name="Namibia",
            capital="Windhoek",
        ),
        Country(
            timezones=["Africa/Niamey"],
            alpha_2_code="NE",
            alpha_3_code="NER",
            continent="Africa",
            name="Niger",
            capital="Niamey",
        ),
        Country(
            timezones=["Africa/Lagos"],
            alpha_2_code="NG",
            alpha_3_code="NGA",
            continent="Africa",
            name="Nigeria",
            capital="Abuja",
        ),
        Country(
            timezones=["America/Managua"],
            alpha_2_code="NI",
            alpha_3_code="NIC",
            continent="North America",
            name="Nicaragua",
            capital="Managua",
        ),
        Country(
            timezones=["Europe/Amsterdam"],
            alpha_2_code="NL",
            alpha_3_code="NLD",
            continent="Europe",
            name="Kingdom of the Netherlands",
            capital="Amsterdam",
        ),
        Country(
            timezones=["Europe/Oslo"],
            alpha_2_code="NO",
            alpha_3_code="NOR",
            continent="Europe",
            name="Norway",
            capital="Oslo",
        ),
        Country(
            timezones=["Asia/Katmandu"],
            alpha_2_code="NP",
            alpha_3_code="NPL",
            continent="Asia",
            name="Nepal",
            capital="Kathmandu",
        ),
        Country(
            timezones=["Pacific/Nauru"],
            alpha_2_code="NR",
            alpha_3_code="NRU",
            continent="Oceania",
            name="Nauru",
            capital="Yaren",
        ),
        Country(
            timezones=["Pacific/Auckland", "Pacific/Chatham"],
            alpha_2_code="NZ",
            alpha_3_code="NZL",
            continent="Oceania",
            name="New Zealand",
            capital="Wellington",
        ),
        Country(
            timezones=["Asia/Muscat"],
            alpha_2_code="OM",
            alpha_3_code="OMN",
            continent="Asia",
            name="Oman",
            capital="Muscat",
        ),
        Country(
            timezones=["America/Panama"],
            alpha_2_code="PA",
            alpha_3_code="PAN",
            continent="North America",
            name="Panama",
            capital="Panama City",
        ),
        Country(
            timezones=["America/Lima"],
            alpha_2_code="PE",
            alpha_3_code="PER",
            continent="South America",
            name="Peru",
            capital="Lima",
        ),
        Country(
            timezones=["Pacific/Port_Moresby"],
            alpha_2_code="PG",
            alpha_3_code="PNG",
            continent="Oceania",
            name="Papua New Guinea",
            capital="Port Moresby",
        ),
        Country(
            timezones=["Asia/Manila"],
            alpha_2_code="PH",
            alpha_3_code="PHL",
            continent="Asia",
            name="Philippines",
            capital="Manila",
        ),
        Country(
            timezones=["Asia/Karachi"],
            alpha_2_code="PK",
            alpha_3_code="PAK",
            continent="Asia",
            name="Pakistan",
            capital="Islamabad",
        ),
        Country(
            timezones=["Europe/Warsaw"],
            alpha_2_code="PL",
            alpha_3_code="POL",
            continent="Europe",
            name="Poland",
            capital="Warsaw",
        ),
        Country(
            timezones=["Europe/Lisbon", "Atlantic/Madeira", "Atlantic/Azores"],
            alpha_2_code="PT",
            alpha_3_code="PRT",
            continent="Europe",
            name="Portugal",
            capital="Lisbon",
        ),
        Country(
            timezones=["Pacific/Palau"],
            alpha_2_code="PW",
            alpha_3_code="PLW",
            continent="Oceania",
            name="Palau",
            capital="Ngerulmud",
        ),
        Country(
            timezones=["America/Asuncion"],
            alpha_2_code="PY",
            alpha_3_code="PRY",
            continent="South America",
            name="Paraguay",
            capital="Asunci\xc3\xb3n",
        ),
        Country(
            timezones=["Asia/Qatar"],
            alpha_2_code="QA",
            alpha_3_code="QAT",
            continent="Asia",
            name="Qatar",
            capital="Doha",
        ),
        Country(
            timezones=["Europe/Bucharest"],
            alpha_2_code="RO",
            alpha_3_code="ROU",
            continent="Europe",
            name="Romania",
            capital="Bucharest",
        ),
        Country(
            timezones=[
                "Europe/Kaliningrad",
                "Europe/Moscow",
                "Europe/Volgograd",
                "Europe/Samara",
                "Asia/Yekaterinburg",
                "Asia/Omsk",
                "Asia/Novosibirsk",
                "Asia/Krasnoyarsk",
                "Asia/Irkutsk",
                "Asia/Yakutsk",
                "Asia/Vladivostok",
                "Asia/Sakhalin",
                "Asia/Magadan",
                "Asia/Kamchatka",
                "Asia/Anadyr",
            ],
            alpha_2_code="RU",
            alpha_3_code="RUS",
            continent="Europe",
            name="Russia",
            capital="Moscow",
        ),
        Country(
            timezones=["Africa/Kigali"],
            alpha_2_code="RW",
            alpha_3_code="RWA",
            continent="Africa",
            name="Rwanda",
            capital="Kigali",
        ),
        Country(
            timezones=["Asia/Riyadh"],
            alpha_2_code="SA",
            alpha_3_code="SAU",
            continent="Asia",
            name="Saudi Arabia",
            capital="Riyadh",
        ),
        Country(
            timezones=["Pacific/Guadalcanal"],
            alpha_2_code="SB",
            alpha_3_code="SLB",
            continent="Oceania",
            name="Solomon Islands",
            capital="Honiara",
        ),
        Country(
            timezones=["Indian/Mahe"],
            alpha_2_code="SC",
            alpha_3_code="SYC",
            continent="Africa",
            name="Seychelles",
            capital="Victoria",
        ),
        Country(
            timezones=["Africa/Khartoum"],
            alpha_2_code="SD",
            alpha_3_code="SDN",
            continent="Africa",
            name="Sudan",
            capital="Khartoum",
        ),
        Country(
            timezones=["Europe/Stockholm"],
            alpha_2_code="SE",
            alpha_3_code="SWE",
            continent="Europe",
            name="Sweden",
            capital="Stockholm",
        ),
        Country(
            timezones=["Asia/Singapore"],
            alpha_2_code="SG",
            alpha_3_code="SGP",
            continent="Asia",
            name="Singapore",
            capital="Singapore",
        ),
        Country(
            timezones=["Europe/Ljubljana"],
            alpha_2_code="SI",
            alpha_3_code="SVN",
            continent="Europe",
            name="Slovenia",
            capital="Ljubljana",
        ),
        Country(
            timezones=["Europe/Bratislava"],
            alpha_2_code="SK",
            alpha_3_code="SVK",
            continent="Europe",
            name="Slovakia",
            capital="Bratislava",
        ),
        Country(
            timezones=["Africa/Freetown"],
            alpha_2_code="SL",
            alpha_3_code="SLE",
            continent="Africa",
            name="Sierra Leone",
            capital="Freetown",
        ),
        Country(
            timezones=["Europe/San_Marino"],
            alpha_2_code="SM",
            alpha_3_code="SMR",
            continent="Europe",
            name="San Marino",
            capital="San Marino",
        ),
        Country(
            timezones=["Africa/Dakar"],
            alpha_2_code="SN",
            alpha_3_code="SEN",
            continent="Africa",
            name="Senegal",
            capital="Dakar",
        ),
        Country(
            timezones=["Africa/Mogadishu"],
            alpha_2_code="SO",
            alpha_3_code="SOM",
            continent="Africa",
            name="Somalia",
            capital="Mogadishu",
        ),
        Country(
            timezones=["America/Paramaribo"],
            alpha_2_code="SR",
            alpha_3_code="SUR",
            continent="South America",
            name="Suriname",
            capital="Paramaribo",
        ),
        Country(
            timezones=["Africa/Sao_Tome"],
            alpha_2_code="ST",
            alpha_3_code="STP",
            continent="Africa",
            name="S\xc3\xa3o Tom\xc3\xa9 and Pr\xc3\xadncipe",
            capital="S\xc3\xa3o Tom\xc3\xa9",
        ),
        Country(
            timezones=["Asia/Damascus"],
            alpha_2_code="SY",
            alpha_3_code="SYR",
            continent="Asia",
            name="Syria",
            capital="Damascus",
        ),
        Country(
            timezones=["Africa/Lome"],
            alpha_2_code="TG",
            alpha_3_code="TGO",
            continent="Africa",
            name="Togo",
            capital="Lom\xc3\xa9",
        ),
        Country(
            timezones=["Asia/Bangkok"],
            alpha_2_code="TH",
            alpha_3_code="THA",
            continent="Asia",
            name="Thailand",
            capital="Bangkok",
        ),
        Country(
            timezones=["Asia/Dushanbe"],
            alpha_2_code="TJ",
            alpha_3_code="TJK",
            continent="Asia",
            name="Tajikistan",
            capital="Dushanbe",
        ),
        Country(
            timezones=["Asia/Ashgabat"],
            alpha_2_code="TM",
            alpha_3_code="TKM",
            continent="Asia",
            name="Turkmenistan",
            capital="Ashgabat",
        ),
        Country(
            timezones=["Africa/Tunis"],
            alpha_2_code="TN",
            alpha_3_code="TUN",
            continent="Africa",
            name="Tunisia",
            capital="Tunis",
        ),
        Country(
            timezones=["Pacific/Tongatapu"],
            alpha_2_code="TO",
            alpha_3_code="TON",
            continent="Oceania",
            name="Tonga",
            capital="Nuku\xca\xbbalofa",
        ),
        Country(
            timezones=["Europe/Istanbul"],
            alpha_2_code="TR",
            alpha_3_code="TUR",
            continent="Asia",
            name="Turkey",
            capital="Ankara",
        ),
        Country(
            timezones=["America/Port_of_Spain"],
            alpha_2_code="TT",
            alpha_3_code="TTO",
            continent="North America",
            name="Trinidad and Tobago",
            capital="Port of Spain",
        ),
        Country(
            timezones=["Pacific/Funafuti"],
            alpha_2_code="TV",
            alpha_3_code="TUV",
            continent="Oceania",
            name="Tuvalu",
            capital="Funafuti",
        ),
        Country(
            timezones=["Africa/Dar_es_Salaam"],
            alpha_2_code="TZ",
            alpha_3_code="TZA",
            continent="Africa",
            name="Tanzania",
            capital="Dodoma",
        ),
        Country(
            timezones=[
                "Europe/Kiev",
                "Europe/Uzhgorod",
                "Europe/Zaporozhye",
                "Europe/Simferopol",
            ],
            alpha_2_code="UA",
            alpha_3_code="UKR",
            continent="Europe",
            name="Ukraine",
            capital="Kiev",
        ),
        Country(
            timezones=["Africa/Kampala"],
            alpha_2_code="UG",
            alpha_3_code="UGA",
            continent="Africa",
            name="Uganda",
            capital="Kampala",
        ),
        Country(
            timezones=[
                "America/New_York",
                "America/Detroit",
                "America/Kentucky/Louisville",
                "America/Kentucky/Monticello",
                "America/Indiana/Indianapolis",
                "America/Indiana/Marengo",
                "America/Indiana/Knox",
                "America/Indiana/Vevay",
                "America/Chicago",
                "America/Indiana/Vincennes",
                "America/Indiana/Petersburg",
                "America/Menominee",
                "America/North_Dakota/Center",
                "America/North_Dakota/New_Salem",
                "America/Denver",
                "America/Boise",
                "America/Shiprock",
                "America/Phoenix",
                "America/Los_Angeles",
                "America/Anchorage",
                "America/Juneau",
                "America/Yakutat",
                "America/Nome",
                "America/Adak",
                "Pacific/Honolulu",
            ],
            alpha_2_code="US",
            alpha_3_code="USA",
            continent="North America",
            name="United States",
            capital="Washington, D.C.",
        ),
        Country(
            timezones=["America/Montevideo"],
            alpha_2_code="UY",
            alpha_3_code="URY",
            continent="South America",
            name="Uruguay",
            capital="Montevideo",
        ),
        Country(
            timezones=["Asia/Samarkand", "Asia/Tashkent"],
            alpha_2_code="UZ",
            alpha_3_code="UZB",
            continent="Asia",
            name="Uzbekistan",
            capital="Tashkent",
        ),
        Country(
            timezones=["Europe/Vatican"],
            alpha_2_code="VA",
            alpha_3_code="VAT",
            continent="Europe",
            name="Vatican City",
            capital="Vatican City",
        ),
        Country(
            timezones=["America/Caracas"],
            alpha_2_code="VE",
            alpha_3_code="VEN",
            continent="South America",
            name="Venezuela",
            capital="Caracas",
        ),
        Country(
            timezones=["Asia/Saigon"],
            alpha_2_code="VN",
            alpha_3_code="VNM",
            continent="Asia",
            name="Vietnam",
            capital="Hanoi",
        ),
        Country(
            timezones=["Pacific/Efate"],
            alpha_2_code="VU",
            alpha_3_code="VUT",
            continent="Oceania",
            name="Vanuatu",
            capital="Port Vila",
        ),
        Country(
            timezones=["Asia/Aden"],
            alpha_2_code="YE",
            alpha_3_code="YEM",
            continent="Asia",
            name="Yemen",
            capital="Sana'a",
        ),
        Country(
            timezones=["Africa/Lusaka"],
            alpha_2_code="ZM",
            alpha_3_code="ZMB",
            continent="Africa",
            name="Zambia",
            capital="Lusaka",
        ),
        Country(
            timezones=["Africa/Harare"],
            alpha_2_code="ZW",
            alpha_3_code="ZWE",
            continent="Africa",
            name="Zimbabwe",
            capital="Harare",
        ),
        Country(
            timezones=["Africa/Algiers"],
            alpha_2_code="DZ",
            alpha_3_code="DZA",
            continent="Africa",
            name="Algeria",
            capital="Algiers",
        ),
        Country(
            timezones=["Europe/Sarajevo"],
            alpha_2_code="BA",
            alpha_3_code="BIH",
            continent="Europe",
            name="Bosnia and Herzegovina",
            capital="Sarajevo",
        ),
        Country(
            timezones=["Asia/Phnom_Penh"],
            alpha_2_code="KH",
            alpha_3_code="KHM",
            continent="Asia",
            name="Cambodia",
            capital="Phnom Penh",
        ),
        Country(
            timezones=["Africa/Bangui"],
            alpha_2_code="CF",
            alpha_3_code="CAF",
            continent="Africa",
            name="Central African Republic",
            capital="Bangui",
        ),
        Country(
            timezones=["Africa/Ndjamena"],
            alpha_2_code="TD",
            alpha_3_code="TCD",
            continent="Africa",
            name="Chad",
            capital="N'Djamena",
        ),
        Country(
            timezones=["Indian/Comoro"],
            alpha_2_code="KM",
            alpha_3_code="COM",
            continent="Africa",
            name="Comoros",
            capital="Moroni",
        ),
        Country(
            timezones=["Europe/Zagreb"],
            alpha_2_code="HR",
            alpha_3_code="HRV",
            continent="Europe",
            name="Croatia",
            capital="Zagreb",
        ),
        Country(
            timezones=["Asia/Dili"],
            alpha_2_code="TL",
            alpha_3_code="TLS",
            continent="Asia",
            name="East Timor",
            capital="Dili",
        ),
        Country(
            timezones=["America/El_Salvador"],
            alpha_2_code="SV",
            alpha_3_code="SLV",
            continent="North America",
            name="El Salvador",
            capital="San Salvador",
        ),
        Country(
            timezones=["Africa/Malabo"],
            alpha_2_code="GQ",
            alpha_3_code="GNQ",
            continent="Africa",
            name="Equatorial Guinea",
            capital="Malabo",
        ),
        Country(
            timezones=["America/Grenada"],
            alpha_2_code="GD",
            alpha_3_code="GRD",
            continent="North America",
            name="Grenada",
            capital="St. George's",
        ),
        Country(
            timezones=[
                "Asia/Almaty",
                "Asia/Qyzylorda",
                "Asia/Aqtobe",
                "Asia/Aqtau",
                "Asia/Oral",
            ],
            alpha_2_code="KZ",
            alpha_3_code="KAZ",
            continent="Asia",
            name="Kazakhstan",
            capital="Astana",
        ),
        Country(
            timezones=["Asia/Vientiane"],
            alpha_2_code="LA",
            alpha_3_code="LAO",
            continent="Asia",
            name="Laos",
            capital="Vientiane",
        ),
        Country(
            timezones=["Pacific/Truk", "Pacific/Ponape", "Pacific/Kosrae"],
            alpha_2_code="FM",
            alpha_3_code="FSM",
            continent="Oceania",
            name="Federated States of Micronesia",
            capital="Palikir",
        ),
        Country(
            timezones=["Europe/Chisinau"],
            alpha_2_code="MD",
            alpha_3_code="MDA",
            continent="Europe",
            name="Moldova",
            capital="Chi\xc5\x9fin\xc4\x83u",
        ),
        Country(
            timezones=["Europe/Monaco"],
            alpha_2_code="MC",
            alpha_3_code="MCO",
            continent="Europe",
            name="Monaco",
            capital="Monaco",
        ),
        Country(
            timezones=["Europe/Podgorica"],
            alpha_2_code="ME",
            alpha_3_code="MNE",
            continent="Europe",
            name="Montenegro",
            capital="Podgorica",
        ),
        Country(
            timezones=["Africa/Casablanca"],
            alpha_2_code="MA",
            alpha_3_code="MAR",
            continent="Africa",
            name="Morocco",
            capital="Rabat",
        ),
        Country(
            timezones=["America/St_Kitts"],
            alpha_2_code="KN",
            alpha_3_code="KNA",
            continent="North America",
            name="Saint Kitts and Nevis",
            capital="Basseterre",
        ),
        Country(
            timezones=["America/St_Lucia"],
            alpha_2_code="LC",
            alpha_3_code="LCA",
            continent="North America",
            name="Saint Lucia",
            capital="Castries",
        ),
        Country(
            timezones=["America/St_Vincent"],
            alpha_2_code="VC",
            alpha_3_code="VCT",
            continent="North America",
            name="Saint Vincent and the Grenadines",
            capital="Kingstown",
        ),
        Country(
            timezones=["Pacific/Apia"],
            alpha_2_code="WS",
            alpha_3_code="WSM",
            continent="Oceania",
            name="Samoa",
            capital="Apia",
        ),
        Country(
            timezones=["Europe/Belgrade"],
            alpha_2_code="RS",
            alpha_3_code="SRB",
            continent="Europe",
            name="Serbia",
            capital="Belgrade",
        ),
        Country(
            timezones=["Africa/Johannesburg"],
            alpha_2_code="ZA",
            alpha_3_code="ZAF",
            continent="Africa",
            name="South Africa",
            capital="Pretoria",
        ),
        Country(
            timezones=["Europe/Madrid", "Africa/Ceuta", "Atlantic/Canary"],
            alpha_2_code="ES",
            alpha_3_code="ESP",
            continent="Europe",
            name="Spain",
            capital="Madrid",
        ),
        Country(
            timezones=["Asia/Colombo"],
            alpha_2_code="LK",
            alpha_3_code="LKA",
            continent="Asia",
            name="Sri Lanka",
            capital="Sri Jayewardenepura Kotte",
        ),
        Country(
            timezones=["Africa/Mbabane"],
            alpha_2_code="SZ",
            alpha_3_code="SWZ",
            continent="Africa",
            name="Swaziland",
            capital="Mbabane",
        ),
        Country(
            timezones=["Europe/Zurich"],
            alpha_2_code="CH",
            alpha_3_code="CHE",
            continent="Europe",
            name="Switzerland",
            capital="Bern",
        ),
        Country(
            timezones=["Asia/Dubai"],
            alpha_2_code="AE",
            alpha_3_code="ARE",
            continent="Asia",
            name="United Arab Emirates",
            capital="Abu Dhabi",
        ),
        Country(
            timezones=["Europe/London"],
            alpha_2_code="GB",
            alpha_3_code="GBR",
            continent="Europe",
            name="United Kingdom",
            capital="London",
        ),
        Country(
            timezones=["Asia/Taipei"],
            alpha_2_code="TW",
            alpha_3_code="TWN",
            continent="Asia",
            name="Taiwan",
            capital="Taipei",
        ),
        Country(
            timezones=["Asia/Gaza", "Asia/Hebron"],
            alpha_2_code="PS",
            alpha_3_code="PSE",
            continent="Asia",
            name="Palestine",
            capital="Ramallah",
        ),
    ]

    regex = re.compile(timedelta_pattern)

    def unix_time(
        self,
        end_datetime: Optional[DateParseType] = None,
        start_datetime: Optional[DateParseType] = None,
    ) -> float:
        """
        Get a timestamp between January 1, 1970 and now, unless passed
        explicit start_datetime or end_datetime values.

        On Windows, the decimal part is always 0.

        :example: 1061306726.6
        """
        start_datetime = self._parse_start_datetime(start_datetime)
        end_datetime = self._parse_end_datetime(end_datetime)
        return float(self._rand_seconds(start_datetime, end_datetime))

    def time_delta(self, end_datetime: Optional[DateParseType] = None) -> timedelta:
        """
        Get a timedelta object
        """
        start_datetime = self._parse_start_datetime("now")
        end_datetime = self._parse_end_datetime(end_datetime)
        seconds = end_datetime - start_datetime

        ts = self._rand_seconds(*sorted([0, seconds]))
        return timedelta(seconds=ts)

    def date_time(
        self,
        tzinfo: Optional[TzInfo] = None,
        end_datetime: Optional[DateParseType] = None,
    ) -> datetime:
        """
        Get a datetime object for a date between January 1, 1970 and now

        :param tzinfo: timezone, instance of datetime.tzinfo subclass
        :example: datetime('2005-08-16 20:39:21')
        :return: datetime
        """
        # NOTE: On windows, the lowest value you can get from windows is 86400
        #       on the first day. Known python issue:
        #       https://bugs.python.org/issue30684
        return datetime(1970, 1, 1, tzinfo=tzinfo) + timedelta(seconds=self.unix_time(end_datetime=end_datetime))

    def date_time_ad(
        self,
        tzinfo: Optional[TzInfo] = None,
        end_datetime: Optional[DateParseType] = None,
        start_datetime: Optional[DateParseType] = None,
    ) -> datetime:
        """
        Get a datetime object for a date between January 1, 001 and now

        :param tzinfo: timezone, instance of datetime.tzinfo subclass
        :example: datetime('1265-03-22 21:15:52')
        :return: datetime
        """

        # 1970-01-01 00:00:00 UTC minus 62135596800 seconds is
        # 0001-01-01 00:00:00 UTC.  Since _parse_end_datetime() is used
        # elsewhere where a default value of 0 is expected, we can't
        # simply change that class method to use this magic number as a
        # default value when None is provided.

        start_time = -62135596800 if start_datetime is None else self._parse_start_datetime(start_datetime)
        end_datetime = self._parse_end_datetime(end_datetime)

        ts = self._rand_seconds(start_time, end_datetime)
        # NOTE: using datetime.fromtimestamp(ts) directly will raise
        #       a "ValueError: timestamp out of range for platform time_t"
        #       on some platforms due to system C functions;
        #       see http://stackoverflow.com/a/10588133/2315612
        # NOTE: On windows, the lowest value you can get from windows is 86400
        #       on the first day. Known python issue:
        #       https://bugs.python.org/issue30684
        return datetime(1970, 1, 1, tzinfo=tzinfo) + timedelta(seconds=ts)

    def iso8601(
        self,
        tzinfo: Optional[TzInfo] = None,
        end_datetime: Optional[DateParseType] = None,
        sep: str = "T",
        timespec: str = "auto",
    ) -> str:
        """
        Get a timestamp in ISO 8601 format (or one of its profiles).

        :param tzinfo: timezone, instance of datetime.tzinfo subclass
        :param sep: separator between date and time, defaults to 'T'
        :param timespec: format specifier for the time part, defaults to 'auto' - see datetime.isoformat() documentation
        :example: '2003-10-21T16:05:52+0000'
        """
        return self.date_time(tzinfo, end_datetime=end_datetime).isoformat(sep, timespec)

    def date(self, pattern: str = "%Y-%m-%d", end_datetime: Optional[DateParseType] = None) -> str:
        """
        Get a date string between January 1, 1970 and now.

        :param pattern: Format of the date (year-month-day by default)
        :example: '2008-11-27'
        :return: Date
        """
        return self.date_time(end_datetime=end_datetime).strftime(pattern)

    def date_object(self, end_datetime: Optional[datetime] = None) -> dtdate:
        """
        Get a date object between January 1, 1970 and now

        :example: datetime.date(2016, 9, 20)
        """
        return self.date_time(end_datetime=end_datetime).date()

    def time(self, pattern: str = "%H:%M:%S", end_datetime: Optional[DateParseType] = None) -> str:
        """
        Get a time string (24h format by default)

        :param pattern: format
        :example: '15:02:34'
        """
        return self.date_time(end_datetime=end_datetime).time().strftime(pattern)

    def time_object(self, end_datetime: Optional[DateParseType] = None) -> dttime:
        """
        Get a time object

        :example: datetime.time(15, 56, 56, 772876)
        """
        return self.date_time(end_datetime=end_datetime).time()

    @classmethod
    def _parse_start_datetime(cls, value: Optional[DateParseType]) -> int:
        if value is None:
            return 0

        return cls._parse_date_time(value)

    @classmethod
    def _parse_end_datetime(cls, value: Optional[DateParseType]) -> int:
        if value is None:
            return datetime_to_timestamp(datetime.now())

        return cls._parse_date_time(value)

    @classmethod
    def _parse_date_string(cls, value: str) -> Dict[str, float]:
        parts = cls.regex.match(value)
        if not parts:
            raise ParseError(f"Can't parse date string `{value}`")
        parts = parts.groupdict()
        time_params: Dict[str, float] = {}
        for name_, param_ in parts.items():
            if param_:
                time_params[name_] = int(param_)

        if "years" in time_params:
            if "days" not in time_params:
                time_params["days"] = 0
            time_params["days"] += 365.24 * time_params.pop("years")
        if "months" in time_params:
            if "days" not in time_params:
                time_params["days"] = 0
            time_params["days"] += 30.42 * time_params.pop("months")

        if not time_params:
            raise ParseError(f"Can't parse date string `{value}`")
        return time_params

    @classmethod
    def _parse_timedelta(cls, value: Union[timedelta, str, float]) -> Union[float, int]:
        if isinstance(value, timedelta):
            return value.total_seconds()
        if isinstance(value, str):
            time_params = cls._parse_date_string(value)
            return timedelta(**time_params).total_seconds()  # type: ignore
        if isinstance(value, (int, float)):
            return value
        raise ParseError(f"Invalid format for timedelta {value!r}")

    @classmethod
    def _parse_date_time(cls, value: DateParseType, tzinfo: Optional[TzInfo] = None) -> int:
        if isinstance(value, (datetime, dtdate)):
            return datetime_to_timestamp(value)
        now = datetime.now(tzinfo)
        if isinstance(value, timedelta):
            return datetime_to_timestamp(now + value)
        if isinstance(value, str):
            if value == "now":
                return datetime_to_timestamp(datetime.now(tzinfo))
            time_params = cls._parse_date_string(value)
            return datetime_to_timestamp(now + timedelta(**time_params))  # type: ignore
        if isinstance(value, int):
            return value
        raise ParseError(f"Invalid format for date {value!r}")

    @classmethod
    def _parse_date(cls, value: DateParseType) -> dtdate:
        if isinstance(value, datetime):
            return value.date()
        elif isinstance(value, dtdate):
            return value
        today = dtdate.today()
        if isinstance(value, timedelta):
            return today + value
        if isinstance(value, str):
            if value in ("today", "now"):
                return today
            time_params = cls._parse_date_string(value)
            return today + timedelta(**time_params)  # type: ignore
        if isinstance(value, int):
            return today + timedelta(value)
        raise ParseError(f"Invalid format for date {value!r}")

    def date_time_between(
        self,
        start_date: DateParseType = "-30y",
        end_date: DateParseType = "now",
        tzinfo: Optional[TzInfo] = None,
    ) -> datetime:
        """
        Get a datetime object based on a random date between two given dates.
        Accepts date strings that can be recognized by strtotime().

        :param start_date: Defaults to 30 years ago
        :param end_date: Defaults to "now"
        :param tzinfo: timezone, instance of datetime.tzinfo subclass
        :example: datetime('1999-02-02 11:42:52')
        :return: datetime
        """
        start_date = self._parse_date_time(start_date, tzinfo=tzinfo)
        end_date = self._parse_date_time(end_date, tzinfo=tzinfo)
        if end_date - start_date <= 1:
            ts = start_date + self.generator.random.random()
        else:
            ts = self._rand_seconds(start_date, end_date)
        if tzinfo is None:
            return datetime(1970, 1, 1, tzinfo=tzinfo) + timedelta(seconds=ts)
        else:
            return (datetime(1970, 1, 1, tzinfo=tzutc()) + timedelta(seconds=ts)).astimezone(tzinfo)

    def date_between(self, start_date: DateParseType = "-30y", end_date: DateParseType = "today") -> dtdate:
        """
        Get a Date object based on a random date between two given dates.
        Accepts date strings that can be recognized by strtotime().

        :param start_date: Defaults to 30 years ago
        :param end_date: Defaults to "today"
        :example: Date('1999-02-02')
        :return: Date
        """

        start_date = self._parse_date(start_date)
        end_date = self._parse_date(end_date)
        return self.date_between_dates(date_start=start_date, date_end=end_date)

    def future_datetime(self, end_date: DateParseType = "+30d", tzinfo: Optional[TzInfo] = None) -> datetime:
        """
        Get a datetime object based on a random date between 1 second form now
        and a given date.
        Accepts date strings that can be recognized by strtotime().

        :param end_date: Defaults to "+30d"
        :param tzinfo: timezone, instance of datetime.tzinfo subclass
        :example: datetime('1999-02-02 11:42:52')
        :return: datetime
        """
        return self.date_time_between(start_date="+1s", end_date=end_date, tzinfo=tzinfo)

    def future_date(self, end_date: DateParseType = "+30d", tzinfo: Optional[TzInfo] = None) -> dtdate:
        """
        Get a Date object based on a random date between 1 day from now and a
        given date.
        Accepts date strings that can be recognized by strtotime().

        :param end_date: Defaults to "+30d"
        :param tzinfo: timezone, instance of datetime.tzinfo subclass
        :example: dtdate('2030-01-01')
        :return: dtdate
        """
        return self.date_between(start_date="+1d", end_date=end_date)

    def past_datetime(self, start_date: DateParseType = "-30d", tzinfo: Optional[TzInfo] = None) -> datetime:
        """
        Get a datetime object based on a random date between a given date and 1
        second ago.
        Accepts date strings that can be recognized by strtotime().

        :param start_date: Defaults to "-30d"
        :param tzinfo: timezone, instance of datetime.tzinfo subclass
        :example: datetime('1999-02-02 11:42:52')
        :return: datetime
        """
        return self.date_time_between(start_date=start_date, end_date="-1s", tzinfo=tzinfo)

    def past_date(self, start_date: DateParseType = "-30d", tzinfo: Optional[TzInfo] = None) -> dtdate:
        """
        Get a Date object based on a random date between a given date and 1 day
        ago.
        Accepts date strings that can be recognized by strtotime().

        :param start_date: Defaults to "-30d"
        :param tzinfo: timezone, instance of datetime.tzinfo subclass
        :example: dtdate('1999-02-02')
        :return: dtdate
        """
        return self.date_between(start_date=start_date, end_date="-1d")

    def date_time_between_dates(
        self,
        datetime_start: Optional[DateParseType] = None,
        datetime_end: Optional[DateParseType] = None,
        tzinfo: Optional[TzInfo] = None,
    ) -> datetime:
        """
        Takes two datetime objects and returns a random datetime between the two
        given datetimes.
        Accepts datetime objects.

        :param datetime_start: datetime
        :param datetime_end: datetime
        :param tzinfo: timezone, instance of datetime.tzinfo subclass
        :example: datetime('1999-02-02 11:42:52')
        :return: datetime
        """
        datetime_start_ = (
            datetime_to_timestamp(datetime.now(tzinfo))
            if datetime_start is None
            else self._parse_date_time(datetime_start)
        )
        datetime_end_ = (
            datetime_to_timestamp(datetime.now(tzinfo)) if datetime_end is None else self._parse_date_time(datetime_end)
        )

        timestamp = self._rand_seconds(datetime_start_, datetime_end_)
        try:
            if tzinfo is None:
                pick = convert_timestamp_to_datetime(timestamp, tzlocal())
                try:
                    pick = pick.astimezone(tzutc()).replace(tzinfo=None)
                except OSError:
                    pass
            else:
                pick = datetime.fromtimestamp(timestamp, tzinfo)
        except OverflowError:
            raise OverflowError(
                "You specified an end date with a timestamp bigger than the maximum allowed on this"
                " system. Please specify an earlier date.",
            )
        return pick

    def date_between_dates(
        self,
        date_start: Optional[DateParseType] = None,
        date_end: Optional[DateParseType] = None,
    ) -> dtdate:
        """
        Takes two Date objects and returns a random date between the two given dates.
        Accepts Date or datetime objects

        :param date_start: Date
        :param date_end: Date
        :return: Date
        """
        return self.date_time_between_dates(date_start, date_end).date()

    def date_time_this_century(
        self,
        before_now: bool = True,
        after_now: bool = False,
        tzinfo: Optional[TzInfo] = None,
    ) -> datetime:
        """
        Gets a datetime object for the current century.

        :param before_now: include days in current century before today
        :param after_now: include days in current century after today
        :param tzinfo: timezone, instance of datetime.tzinfo subclass
        :example: datetime('2012-04-04 11:02:02')
        :return: datetime
        """
        now = datetime.now(tzinfo)
        this_century_start = datetime(now.year - (now.year % 100), 1, 1, tzinfo=tzinfo)
        next_century_start = datetime(min(this_century_start.year + 100, MAXYEAR), 1, 1, tzinfo=tzinfo)

        if before_now and after_now:
            return self.date_time_between_dates(this_century_start, next_century_start, tzinfo)
        elif not before_now and after_now:
            return self.date_time_between_dates(now, next_century_start, tzinfo)
        elif not after_now and before_now:
            return self.date_time_between_dates(this_century_start, now, tzinfo)
        else:
            return now

    def date_time_this_decade(
        self,
        before_now: bool = True,
        after_now: bool = False,
        tzinfo: Optional[TzInfo] = None,
    ) -> datetime:
        """
        Gets a datetime object for the decade year.

        :param before_now: include days in current decade before today
        :param after_now: include days in current decade after today
        :param tzinfo: timezone, instance of datetime.tzinfo subclass
        :example: datetime('2012-04-04 11:02:02')
        :return: datetime
        """
        now = datetime.now(tzinfo)
        this_decade_start = datetime(now.year - (now.year % 10), 1, 1, tzinfo=tzinfo)
        next_decade_start = datetime(min(this_decade_start.year + 10, MAXYEAR), 1, 1, tzinfo=tzinfo)

        if before_now and after_now:
            return self.date_time_between_dates(this_decade_start, next_decade_start, tzinfo)
        elif not before_now and after_now:
            return self.date_time_between_dates(now, next_decade_start, tzinfo)
        elif not after_now and before_now:
            return self.date_time_between_dates(this_decade_start, now, tzinfo)
        else:
            return now

    def date_time_this_year(
        self,
        before_now: bool = True,
        after_now: bool = False,
        tzinfo: Optional[TzInfo] = None,
    ) -> datetime:
        """
        Gets a datetime object for the current year.

        :param before_now: include days in current year before today
        :param after_now: include days in current year after today
        :param tzinfo: timezone, instance of datetime.tzinfo subclass
        :example: datetime('2012-04-04 11:02:02')
        :return: datetime
        """
        now = datetime.now(tzinfo)
        this_year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        next_year_start = datetime(now.year + 1, 1, 1, tzinfo=tzinfo)

        if before_now and after_now:
            return self.date_time_between_dates(this_year_start, next_year_start, tzinfo)
        elif not before_now and after_now:
            return self.date_time_between_dates(now, next_year_start, tzinfo)
        elif not after_now and before_now:
            return self.date_time_between_dates(this_year_start, now, tzinfo)
        else:
            return now

    def date_time_this_month(
        self,
        before_now: bool = True,
        after_now: bool = False,
        tzinfo: Optional[TzInfo] = None,
    ) -> datetime:
        """
        Gets a datetime object for the current month.

        :param before_now: include days in current month before today
        :param after_now: include days in current month after today
        :param tzinfo: timezone, instance of datetime.tzinfo subclass
        :example: datetime('2012-04-04 11:02:02')
        :return: datetime
        """
        now = datetime.now(tzinfo)
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        next_month_start = this_month_start + relativedelta.relativedelta(months=1)
        if before_now and after_now:
            return self.date_time_between_dates(this_month_start, next_month_start, tzinfo)
        elif not before_now and after_now:
            return self.date_time_between_dates(now, next_month_start, tzinfo)
        elif not after_now and before_now:
            return self.date_time_between_dates(this_month_start, now, tzinfo)
        else:
            return now

    def date_this_century(self, before_today: bool = True, after_today: bool = False) -> dtdate:
        """
        Gets a Date object for the current century.

        :param before_today: include days in current century before today
        :param after_today: include days in current century after today
        :example: Date('2012-04-04')
        :return: Date
        """
        today = dtdate.today()
        this_century_start = dtdate(today.year - (today.year % 100), 1, 1)
        next_century_start = dtdate(this_century_start.year + 100, 1, 1)

        if before_today and after_today:
            return self.date_between_dates(this_century_start, next_century_start)
        elif not before_today and after_today:
            return self.date_between_dates(today, next_century_start)
        elif not after_today and before_today:
            return self.date_between_dates(this_century_start, today)
        else:
            return today

    def date_this_decade(self, before_today: bool = True, after_today: bool = False) -> dtdate:
        """
        Gets a Date object for the decade year.

        :param before_today: include days in current decade before today
        :param after_today: include days in current decade after today
        :example: Date('2012-04-04')
        :return: Date
        """
        today = dtdate.today()
        this_decade_start = dtdate(today.year - (today.year % 10), 1, 1)
        next_decade_start = dtdate(this_decade_start.year + 10, 1, 1)

        if before_today and after_today:
            return self.date_between_dates(this_decade_start, next_decade_start)
        elif not before_today and after_today:
            return self.date_between_dates(today, next_decade_start)
        elif not after_today and before_today:
            return self.date_between_dates(this_decade_start, today)
        else:
            return today

    def date_this_year(self, before_today: bool = True, after_today: bool = False) -> dtdate:
        """
        Gets a Date object for the current year.

        :param before_today: include days in current year before today
        :param after_today: include days in current year after today
        :example: Date('2012-04-04')
        :return: Date
        """
        today = dtdate.today()
        this_year_start = today.replace(month=1, day=1)
        next_year_start = dtdate(today.year + 1, 1, 1)

        if before_today and after_today:
            return self.date_between_dates(this_year_start, next_year_start)
        elif not before_today and after_today:
            return self.date_between_dates(today, next_year_start)
        elif not after_today and before_today:
            return self.date_between_dates(this_year_start, today)
        else:
            return today

    def date_this_month(self, before_today: bool = True, after_today: bool = False) -> dtdate:
        """
        Gets a Date object for the current month.

        :param before_today: include days in current month before today
        :param after_today: include days in current month after today
        :example: dtdate('2012-04-04')
        :return: dtdate
        """
        today = dtdate.today()
        this_month_start = today.replace(day=1)

        next_month_start = this_month_start + relativedelta.relativedelta(months=1)
        if before_today and after_today:
            return self.date_between_dates(this_month_start, next_month_start)
        elif not before_today and after_today:
            return self.date_between_dates(today, next_month_start)
        elif not after_today and before_today:
            return self.date_between_dates(this_month_start, today)
        else:
            return today

    def time_series(
        self,
        start_date: DateParseType = "-30d",
        end_date: DateParseType = "now",
        precision: Optional[float] = None,
        distrib: Optional[Callable[[datetime], float]] = None,
        tzinfo: Optional[TzInfo] = None,
    ) -> Iterator[Tuple[datetime, Any]]:
        """
        Returns a generator yielding tuples of ``(<datetime>, <value>)``.

        The data points will start at ``start_date``, and be at every time interval specified by
        ``precision``.
        ``distrib`` is a callable that accepts ``<datetime>`` and returns ``<value>``

        """
        start_date_ = self._parse_date_time(start_date, tzinfo=tzinfo)
        end_date_ = self._parse_date_time(end_date, tzinfo=tzinfo)

        if end_date_ < start_date_:
            raise ValueError("`end_date` must be greater than `start_date`.")

        precision_ = self._parse_timedelta((end_date_ - start_date_) / 30 if precision is None else precision)
        if distrib is None:

            def distrib(dt):
                return self.generator.random.uniform(0, precision_)  # noqa

        if not callable(distrib):
            raise ValueError(f"`distrib` must be a callable. Got {distrib} instead.")

        datapoint: Union[float, int] = start_date_
        while datapoint < end_date_:
            dt = timestamp_to_datetime(datapoint, tzinfo)
            datapoint += precision_
            yield (dt, distrib(dt))

    def am_pm(self) -> str:
        return self.date("%p")

    def day_of_month(self) -> str:
        return self.date("%d")

    def day_of_week(self) -> str:
        return self.date("%A")

    def month(self) -> str:
        return self.date("%m")

    def month_name(self) -> str:
        return self.date("%B")

    def year(self) -> str:
        return self.date("%Y")

    def century(self) -> str:
        """
        :example: 'XVII'
        """
        return self.random_element(self.centuries)

    def timezone(self) -> str:
        return self.generator.random.choice(self.random_element(self.countries).timezones)  # type: ignore

    def pytimezone(self, *args: Any, **kwargs: Any) -> Optional[TzInfo]:
        """
        Generate a random timezone (see `faker.timezone` for any args)
        and return as a python object usable as a `tzinfo` to `datetime`
        or other fakers.

        :example: faker.pytimezone()
        :return: dateutil.tz.tz.tzfile
        """
        return gettz(self.timezone(*args, **kwargs))  # type: ignore

    def date_of_birth(
        self,
        tzinfo: Optional[TzInfo] = None,
        minimum_age: int = 0,
        maximum_age: int = 115,
    ) -> dtdate:
        """
        Generate a random date of birth represented as a Date object,
        constrained by optional miminimum_age and maximum_age
        parameters.

        :param tzinfo: Defaults to None.
        :param minimum_age: Defaults to 0.
        :param maximum_age: Defaults to 115.

        :example: Date('1979-02-02')
        :return: Date
        """

        if not isinstance(minimum_age, int):
            raise TypeError("minimum_age must be an integer.")

        if not isinstance(maximum_age, int):
            raise TypeError("maximum_age must be an integer.")

        if maximum_age < 0:
            raise ValueError("maximum_age must be greater than or equal to zero.")

        if minimum_age < 0:
            raise ValueError("minimum_age must be greater than or equal to zero.")

        if minimum_age > maximum_age:
            raise ValueError("minimum_age must be less than or equal to maximum_age.")

        # In order to return the full range of possible dates of birth, add one
        # year to the potential age cap and subtract one day if we land on the
        # boundary.

        now = datetime.now(tzinfo).date()
        start_date = change_year(now, -(maximum_age + 1))
        end_date = change_year(now, -minimum_age)

        dob = self.date_time_ad(tzinfo=tzinfo, start_datetime=start_date, end_datetime=end_date).date()

        return dob if dob != start_date else dob + timedelta(days=1)


def convert_timestamp_to_datetime(timestamp: Union[int, float], tzinfo: TzInfo) -> datetime:
    import datetime as dt

    if timestamp >= 0:
        return dt.datetime.fromtimestamp(timestamp, tzinfo)
    else:
        return dt.datetime(1970, 1, 1, tzinfo=tzinfo) + dt.timedelta(seconds=int(timestamp))
