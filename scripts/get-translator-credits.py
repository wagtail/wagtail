import re
import subprocess
from collections import defaultdict
from io import open

from babel import Locale

authors_by_locale = defaultdict(set)

file_listing = subprocess.Popen(
    "find ./wagtail -iname *.po", shell=True, stdout=subprocess.PIPE
)

for file_listing_line in file_listing.stdout:
    filename = file_listing_line.strip()

    # extract locale string from filename
    locale = re.search(r"locale/(\w+)/LC_MESSAGES", str(filename)).group(1)
    if locale == "en":
        continue

    # read author list from each file
    with open(filename, "rt") as f:
        has_found_translators_heading = False
        for line in f:
            line = line.strip()
            if line.startswith("#"):
                if has_found_translators_heading:
                    author_match = re.match(r"\# (.*), [\d\-]+", line)
                    if not author_match:
                        break
                    author = author_match.group(1)
                    authors_by_locale[locale].add(author)
                elif line.startswith("# Translators:"):
                    has_found_translators_heading = True
            else:
                if has_found_translators_heading:
                    break
                else:
                    raise Exception("No 'Translators:' heading found in %s" % filename)


LANGUAGE_OVERRIDES = {
    "tet": "Tetum",
    "ht": "Haitian",
}


def get_language_name(locale_string):
    try:
        return LANGUAGE_OVERRIDES[locale_string]
    except KeyError:
        return Locale.parse(locale_string).english_name


language_names = [
    (get_language_name(locale_string), locale_string)
    for locale_string in authors_by_locale.keys()
]
language_names.sort()

for (language_name, locale) in language_names:
    print(("%s - %s" % (language_name, locale)))  # noqa
    print("-----")  # noqa
    for author in sorted(authors_by_locale[locale]):
        print(author)  # noqa
    print("")  # noqa
