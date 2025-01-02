"""
Utility to download and generate timezone translations for the Wagtail admin
from the Unicode Consortium CLDR. This only needs to be run if
WAGTAILADMIN_PROVIDED_LANGUAGES changes or if timezones in pytz change.

This script will output ``.po`` files with mostly automated translations.
Language experts should review these and make necessary adjustments.
"""

# Import from standard library.
import datetime
import json
import os
import urllib

# Setup django so we can import things from Wagtail.
import django  # noqa

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wagtail.test.settings")
django.setup()


import polib  # noqa
import pytz  # noqa
from wagtail.admin.localization import WAGTAILADMIN_PROVIDED_LANGUAGES  # noqa


URL = "https://raw.githubusercontent.com/unicode-org/cldr-json/39.0.0/cldr-json"


# Since CLDR territories do not exactly match CLDR timezone territories, use
# these similar replacements which *do* exist in CLDR territory database.
TERRITORY_ALIASES = {
    # "Timezone territory": "CLDR territory"
    "America": "Americas",
}


# Timezones which may be formatted differently between pytz and CLDR. Note that
# the pytz zone is always retained as the value; the CLDR zone or metazone is
# used purely for translation purposes. Aliases and deprecations can be looked
# up here: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
ZONE_ALIASES = {
    # "pytz zone": "CLDR zone"
    "Africa/Asmara": "Africa/Nairobi",
    "America/Argentina/Buenos_Aires": "America/Buenos_Aires",
    "America/Argentina/Catamarca": "America/Catamarca",
    "America/Argentina/Cordoba": "America/Cordoba",
    "America/Argentina/Jujuy": "America/Jujuy",
    "America/Argentina/Mendoza": "America/Mendoza",
    "America/Atikokan": "America/Coral_Harbour",
    "America/Indiana/Indianapolis": "America/Indianapolis",
    "America/Kentucky/Louisville": "America/Louisville",
    "America/Knox_IN": "America/Indiana/Knox",
    "Asia/Ho_Chi_Minh": "Asia/Saigon",
    "Asia/Kathmandu": "Asia/Katmandu",
    "Asia/Kolkata": "Asia/Calcutta",
    "Asia/Yangon": "Asia/Rangoon",
    "Atlantic/Faroe": "Atlantic/Faeroe",
    "Pacific/Chuuk": "Pacific/Truk",
    "Pacific/Pohnpei": "Pacific/Ponape",
    "UTC": "Etc/UTC",
}
METAZONE_ALIASES = {
    # "pytz zone": "CLDR metazone"
    "Canada/Atlantic": "Atlantic",
    "Canada/Central": "America_Central",
    "Canada/Eastern": "America_Eastern",
    "Canada/Mountain": "America_Mountain",
    "Canada/Newfoundland": "Newfoundland",
    "Canada/Pacific": "America_Pacific",
    "GMT": "GMT",
    "US/Alaska": "Alaska",
    "US/Central": "America_Central",
    "US/Eastern": "America_Eastern",
    "US/Hawaii": "Hawaii_Aleutian",
    "US/Mountain": "America_Mountain",
    "US/Pacific": "America_Pacific",
}


# Since timezones are formatted as ``Territory/City``, but the CLDR database
# only provides translations for the City, first create a map of territories
# based on the English version. Then flip {key:value} so they are keyed by
# territory name instead of ID (so we can easily look up the IDs later).
TERRITORY_MAP = {}
uri = f"{URL}/cldr-localenames-full/main/en/territories.json"
with urllib.request.urlopen(uri) as r:
    data = json.loads(r.read().decode("utf-8"))
    data = data["main"]["en"]["localeDisplayNames"]["territories"]
    for key in data:
        value = data[key]
        TERRITORY_MAP[value] = key


def _get_city(z: dict) -> str:
    """
    Gets the exemplar city, long/generic, or long/standard name within a given
    CLDR zone dictionary.
    """
    city = z.get("exemplarCity", "")
    if not city and z.get("long"):
        city = z["long"].get("generic", z["long"].get("standard", ""))
    return city


def _get_territory(t: dict, name: str) -> str:
    """
    Gets the translated territory name from a given CDLR territory dictionary.
    """
    ter_id = TERRITORY_MAP.get(TERRITORY_ALIASES.get(name, name))
    return t.get(ter_id, "")


def _download_json(uri: str) -> dict:
    """
    Downloads the requested URI and returns as a json-parsed dictionary.
    """
    with urllib.request.urlopen(uri) as r:
        data = json.loads(r.read().decode("utf-8"))
    return data


# For each language supported by Wagtail admin, download territory and timezone
# translations from the Unicode consortium and convert it into a Python message
# file (``.po`` and ``.mo``).
time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M%z")
for item in WAGTAILADMIN_PROVIDED_LANGUAGES:
    lang = item[0]

    # Download territories in the language.
    cldr_territories = {}
    print(f"Downloading territories for {lang}...")  # noqa: T201
    uri = f"{URL}/cldr-localenames-full/main/{lang}/territories.json"
    try:
        data = _download_json(uri)
    except urllib.error.HTTPError:
        # Try alternate form of language...
        lang = lang.split("-")[0]
        uri = f"{URL}/cldr-localenames-full/main/{lang}/territories.json"
        data = _download_json(uri)

    cldr_territories = data["main"][lang]["localeDisplayNames"]["territories"]

    # Download timezones in the language.
    cldr_timezones = {}
    cldr_metazones = {}
    print(f"Downloading timezones for {lang}...")  # noqa: T201
    uri = f"{URL}/cldr-dates-full/main/{lang}/timeZoneNames.json"
    try:
        data = _download_json(uri)
    except urllib.error.HTTPError:
        # Try alternate form of language...
        lang = lang.split("-")[0]
        uri = f"{URL}/cldr-dates-full/main/{lang}/timeZoneNames.json"
        data = _download_json(uri)

    cldr_timezones = data["main"][lang]["dates"]["timeZoneNames"]["zone"]
    cldr_metazones = data["main"][lang]["dates"]["timeZoneNames"]["metazone"]

    # Make the message file.
    po = polib.POFile()
    po.metadata = {
        "Project-Id-Version": "Wagtail",
        "PO-Revision-Date": time,
        "Last-Translator": "translate.py",
        "Language-Team": (
            "The Unicode Consortium CLDR " "<https://github.com/unicode-org/cldr-json>"
        ),
        "MIME-Version": "1.0",
        "Content-Type": "text/plain; charset=utf-8",
        "Content-Transfer-Encoding": "8bit",
    }

    # Add entry for each common timezone.
    for pytz_name in pytz.common_timezones:
        # print(pytz_name)
        timezone = ZONE_ALIASES.get(pytz_name, pytz_name)
        metazone = METAZONE_ALIASES.get(pytz_name, None)
        zones = timezone.split("/")

        trans_territory = ""
        trans_city = ""

        # If this is a metazone, process it separately.
        if metazone:
            # Translate first part of zone as territory.
            ter = _get_territory(cldr_territories, zones[0])
            if ter:
                trans_territory += f"{ter}/"

            # Translate the metazone as a city.
            trans_city = _get_city(cldr_metazones[metazone])

        else:
            # Traverse variable number of zones to get to the city, e.g.
            # America/Indiana/East
            exists = True
            z = cldr_timezones
            for subzone in zones:
                try:
                    z = z[subzone]
                except KeyError:
                    print(f"WARNING: '{timezone}' not found in '{lang}'.")  # noqa: T201
                    exists = False

                # If this zone does not have an exemplarCity/long, try to
                # translate it from the regions.
                if not exists or not (z.get("exemplarCity") or z.get("long")):
                    ter = _get_territory(cldr_territories, subzone)
                    if ter:
                        trans_territory += f"{ter}/"

                if not exists:
                    break

            # If this zone exists, get the exemplarCity or the long generic or
            # long standard name.
            if exists:
                trans_city = _get_city(z)

        # Show UTC as "UTC/<name>" rather than our usual format of "Etc/<name>".
        if pytz_name == "UTC":
            trans_territory = "UTC/"

        # Re-combine using translated territory and city.
        trans_entry = pytz_name
        if trans_territory and trans_city:
            trans_entry = f"{trans_territory}{trans_city}"
        elif trans_territory:
            trans_entry = f"{trans_territory}{zones[-1]}"
        elif trans_city:
            trans_entry = f"{zones[0]}/{trans_city}"

        entry = polib.POEntry(msgid=pytz_name, msgstr=trans_entry)
        po.append(entry)

    # Save the message file.
    path = os.path.join(
        os.path.dirname(__name__),
        "wagtail",
        "admin",
        "locale",
        lang,
        "LC_MESSAGES",
    )
    os.makedirs(path, exist_ok=True)
    po.save(os.path.join(path, "timezones.po"))
    po.save_as_mofile(os.path.join(path, "timezones.mo"))
